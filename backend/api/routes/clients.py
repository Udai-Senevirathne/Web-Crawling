"""
Client management API endpoints (Super Admin only).
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime
from bson import ObjectId
import logging

from backend.models.client import ClientCreate, ClientUpdate, ClientOut, RAGConfig
from backend.services.auth import require_superadmin
from backend.services.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


def serialize_client(client_doc) -> dict:
    """Convert MongoDB document to API response format."""
    if not client_doc:
        return None
    
    client_doc["id"] = str(client_doc.pop("_id"))
    
    # Ensure rag_config has all fields
    if "rag_config" not in client_doc or not client_doc["rag_config"]:
        client_doc["rag_config"] = RAGConfig().dict()
    
    return client_doc


@router.post("/clients", response_model=ClientOut)
async def create_client(client: ClientCreate, user=Depends(require_superadmin)):
    """
    Create a new client (Super Admin only).
    """
    db = get_db()
    
    # Check if enl_id already exists
    existing = db.clients.find_one({"enl_id": client.enl_id})
    if existing:
        raise HTTPException(status_code=400, detail="Client with this ENL ID already exists")
    
    # Prepare client document
    client_doc = {
        "name": client.name,
        "enl_id": client.enl_id,
        "rag_config": client.rag_config.dict() if client.rag_config else RAGConfig().dict(),
        "status": client.status,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "document_count": 0
    }
    
    # Insert into database
    result = db.clients.insert_one(client_doc)
    client_doc["_id"] = result.inserted_id
    
    return ClientOut(**serialize_client(client_doc))


@router.get("/clients", response_model=List[ClientOut])
async def list_clients(user=Depends(require_superadmin)):
    """
    List all clients (Super Admin only).
    """
    db = get_db()
    clients = list(db.clients.find().sort("created_at", -1))
    
    return [ClientOut(**serialize_client(c)) for c in clients]


@router.get("/clients/{client_id}", response_model=ClientOut)
async def get_client(client_id: str, user=Depends(require_superadmin)):
    """
    Get client details (Super Admin only).
    """
    db = get_db()
    
    try:
        client = db.clients.find_one({"_id": ObjectId(client_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid client ID format")
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return ClientOut(**serialize_client(client))


@router.put("/clients/{client_id}", response_model=ClientOut)
async def update_client(client_id: str, client_update: ClientUpdate, user=Depends(require_superadmin)):
    """
    Update client information (Super Admin only).
    """
    db = get_db()
    
    try:
        obj_id = ObjectId(client_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid client ID format")
    
    # Check if client exists
    existing = db.clients.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Prepare update data
    update_data = {
        "updated_at": datetime.utcnow()
    }
    
    if client_update.name is not None:
        update_data["name"] = client_update.name
    if client_update.rag_config is not None:
        update_data["rag_config"] = client_update.rag_config.dict()
    if client_update.status is not None:
        update_data["status"] = client_update.status
    
    # Update in database
    db.clients.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )
    
    # Fetch updated document
    updated_client = db.clients.find_one({"_id": obj_id})
    
    return ClientOut(**serialize_client(updated_client))


@router.delete("/clients/{client_id}")
async def delete_client(client_id: str, user=Depends(require_superadmin)):
    """
    Delete a client (Super Admin only).
    
    WARNING: This will delete all associated data including users and documents.
    """
    db = get_db()
    
    try:
        obj_id = ObjectId(client_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid client ID format")
    
    # Check if client exists
    client = db.clients.find_one({"_id": obj_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    enl_id = client.get("enl_id")
    
    # Delete associated users
    user_result = db.users.delete_many({"client_id": enl_id})
    
    # Delete client document
    db.clients.delete_one({"_id": obj_id})
    
    return {
        "message": f"Client '{client.get('name')}' deleted successfully",
        "deleted_users": user_result.deleted_count
    }


@router.get("/clients/{client_id}/stats")
async def get_client_stats(client_id: str, user=Depends(require_superadmin)):
    """
    Get statistics for a specific client (Super Admin only).
    """
    logger.debug("get_client_stats called for client_id=%s", client_id)
    db = get_db()
    
    try:
        obj_id = ObjectId(client_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid client ID format")
    
    client = db.clients.find_one({"_id": obj_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    enl_id = client.get("enl_id")
    
    # Get user count
    user_count = db.users.count_documents({"client_id": enl_id})
    
    # Get chat history count
    chat_count = db.chat_history.count_documents({"client_id": enl_id}) if "chat_history" in db.list_collection_names() else 0
    
    return {
        "client_id": client_id,
        "client_name": client.get("name"),
        "enl_id": enl_id,
        "user_count": user_count,
        "chat_session_count": chat_count,
        "document_count": client.get("document_count", 0),
        "status": client.get("status"),
        "created_at": client.get("created_at")
    }
