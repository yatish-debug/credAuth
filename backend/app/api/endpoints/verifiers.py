from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.domain import User
from app.schemas.domain import UserResponse, VerifierAdminCreate, VerifierAdminUpdate
from app.api.deps import get_current_active_user, require_role

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def list_authorized_verifiers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "INSTITUTION_ADMIN"]))
):
    """
    List all administrator-created and approved verifier accounts.
    """
    return db.query(User).filter(User.role == "VERIFIER").order_by(User.id.desc()).all()

@router.post("/", response_model=UserResponse)
def create_authorized_verifier(
    verifier_in: VerifierAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "INSTITUTION_ADMIN"]))
):
    """
    Admin-only: Create and assign login credentials for an authorized verifier / recruiter / auditor.
    """
    existing = db.query(User).filter(User.email == verifier_in.email).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A user with this email address already exists in the system."
        )
        
    new_verifier = User(
        name=verifier_in.name,
        email=verifier_in.email,
        password_hash=get_password_hash(verifier_in.password),
        role="VERIFIER",
        organization=verifier_in.organization or "Independent Auditor",
        is_active=verifier_in.is_active,
        institution_id=current_user.institution_id if current_user.role == "INSTITUTION_ADMIN" else None
    )
    db.add(new_verifier)
    db.commit()
    db.refresh(new_verifier)
    
    return new_verifier

@router.put("/{verifier_id}", response_model=UserResponse)
def update_authorized_verifier(
    verifier_id: int,
    verifier_in: VerifierAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "INSTITUTION_ADMIN"]))
):
    """
    Admin-only: Update verifier profile, status, organization, or reset password.
    """
    verifier = db.query(User).filter(User.id == verifier_id, User.role == "VERIFIER").first()
    if not verifier:
        raise HTTPException(status_code=404, detail="Verifier account not found")
        
    if verifier_in.name is not None:
        verifier.name = verifier_in.name
    if verifier_in.email is not None:
        # Check if email is already taken by someone else
        existing = db.query(User).filter(User.email == verifier_in.email, User.id != verifier_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="This email is already in use.")
        verifier.email = verifier_in.email
    if verifier_in.organization is not None:
        verifier.organization = verifier_in.organization
    if verifier_in.is_active is not None:
        verifier.is_active = verifier_in.is_active
    if verifier_in.password:
        verifier.password_hash = get_password_hash(verifier_in.password)
        
    db.commit()
    db.refresh(verifier)
    return verifier

@router.delete("/{verifier_id}")
def delete_authorized_verifier(
    verifier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "INSTITUTION_ADMIN"]))
):
    """
    Admin-only: Revoke / delete authorized verifier credentials.
    """
    verifier = db.query(User).filter(User.id == verifier_id, User.role == "VERIFIER").first()
    if not verifier:
        raise HTTPException(status_code=404, detail="Verifier account not found")
        
    db.delete(verifier)
    db.commit()
    return {"status": "success", "message": "Verifier account revoked successfully."}
