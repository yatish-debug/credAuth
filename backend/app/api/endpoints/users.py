import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import get_password_hash, get_role_permissions
from app.models.domain import User, Organization
from app.api import deps

router = APIRouter()

class UserCreateRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str # SUPER_ADMIN, ORGANIZATION_ADMIN, CREDENTIAL_ISSUER, VERIFICATION_OFFICER, AUDITOR
    organization_id: Optional[int] = None
    permissions: Optional[List[str]] = None

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    organization_id: Optional[int] = None
    is_active: Optional[bool] = None
    permissions: Optional[List[str]] = None

class UserDetailResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    organization_id: Optional[int] = None
    organization_name: Optional[str] = None
    is_active: bool
    permissions: Optional[List[str]] = None

    class Config:
        from_attributes = True

@router.get("", response_model=List[UserDetailResponse])
@router.get("/", response_model=List[UserDetailResponse])
def list_users(
    role: Optional[str] = None,
    organization_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    """
    List users. Super Admin sees all users across the platform.
    Organization Admin sees only users within their own organization.
    """
    query = db.query(User)
    
    if current_user.role != "SUPER_ADMIN":
        query = query.filter(User.institution_id == current_user.institution_id)
    else:
        if organization_id:
            query = query.filter(User.institution_id == organization_id)
            
    if role and role != "ALL":
        query = query.filter(User.role == role)
        
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((User.name.ilike(s)) | (User.email.ilike(s)))
        
    users = query.order_by(User.id.desc()).all()
    
    results = []
    for u in users:
        org_name = None
        if u.institution_id:
            org = db.query(Organization).filter(Organization.id == u.institution_id).first()
            org_name = org.name if org else None
            
        perms = []
        if u.permissions:
            try:
                perms = json.loads(u.permissions)
            except Exception:
                perms = []
        if not perms:
            perms = get_role_permissions(u.role)
            
        results.append(UserDetailResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role,
            organization_id=u.institution_id,
            organization_name=org_name,
            is_active=u.is_active,
            permissions=perms
        ))
        
    return results

@router.post("", response_model=UserDetailResponse)
@router.post("/", response_model=UserDetailResponse)
def create_user(
    user_in: UserCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    """
    Create a new user.
    - Super Admin can create any role for any organization (or platform-wide).
    - Organization Admin can create users only for their own organization.
    """
    # Check if email is already registered
    existing = db.query(User).filter(User.email == user_in.email.strip().lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email address already exists.")
        
    # Check organization assignment
    org_id = user_in.organization_id
    if current_user.role != "SUPER_ADMIN":
        org_id = current_user.institution_id
        if user_in.role == "SUPER_ADMIN":
            raise HTTPException(status_code=403, detail="Only Super Admin can create other Super Admin accounts.")
            
    org_name = None
    if org_id:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail=f"Organization ID {org_id} does not exist.")
        org_name = org.name
        
    # Set default permissions if not provided
    perms = user_in.permissions or get_role_permissions(user_in.role)
    
    new_user = User(
        name=user_in.name.strip(),
        email=user_in.email.strip().lower(),
        password_hash=get_password_hash(user_in.password),
        role=user_in.role.upper(),
        institution_id=org_id,
        is_active=True,
        permissions=json.dumps(perms) if perms else None
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    deps.log_audit_trail(
        db=db,
        action="USER_CREATED",
        resource="USER",
        resource_id=str(new_user.id),
        user_id=current_user.id,
        organization_id=org_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"email": new_user.email, "role": new_user.role, "organization_id": org_id}
    )
    
    return UserDetailResponse(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        role=new_user.role,
        organization_id=new_user.institution_id,
        organization_name=org_name,
        is_active=new_user.is_active,
        permissions=perms
    )

@router.get("/{user_id}", response_model=UserDetailResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
        
    if current_user.role != "SUPER_ADMIN" and target.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Access denied to users of other organizations.")
        
    org = db.query(Organization).filter(Organization.id == target.institution_id).first() if target.institution_id else None
    
    perms = []
    if target.permissions:
        try:
            perms = json.loads(target.permissions)
        except Exception:
            perms = []
    if not perms:
        perms = get_role_permissions(target.role)
        
    return UserDetailResponse(
        id=target.id,
        email=target.email,
        name=target.name,
        role=target.role,
        organization_id=target.institution_id,
        organization_name=org.name if org else None,
        is_active=target.is_active,
        permissions=perms
    )

@router.patch("/{user_id}", response_model=UserDetailResponse)
def update_user(
    user_id: int,
    user_in: UserUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
        
    if current_user.role != "SUPER_ADMIN" and target.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Access denied to edit users of other organizations.")
        
    if user_in.name:
        target.name = user_in.name.strip()
    if user_in.email:
        existing = db.query(User).filter(User.email == user_in.email.strip().lower(), User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="This email is already taken by another user.")
        target.email = user_in.email.strip().lower()
    if user_in.password:
        target.password_hash = get_password_hash(user_in.password)
    if user_in.role and current_user.role == "SUPER_ADMIN":
        target.role = user_in.role.upper()
    if user_in.organization_id is not None and current_user.role == "SUPER_ADMIN":
        target.institution_id = user_in.organization_id
    if user_in.is_active is not None:
        if target.id == current_user.id and not user_in.is_active:
            raise HTTPException(status_code=400, detail="You cannot disable your own active administrator account.")
        target.is_active = user_in.is_active
    if user_in.permissions:
        target.permissions = json.dumps(user_in.permissions)
        
    db.commit()
    db.refresh(target)
    
    deps.log_audit_trail(
        db=db,
        action="USER_UPDATED",
        resource="USER",
        resource_id=str(target.id),
        user_id=current_user.id,
        organization_id=target.institution_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"user_id": target.id, "email": target.email, "role": target.role}
    )
    
    org = db.query(Organization).filter(Organization.id == target.institution_id).first() if target.institution_id else None
    perms = json.loads(target.permissions) if target.permissions else get_role_permissions(target.role)
    
    return UserDetailResponse(
        id=target.id,
        email=target.email,
        name=target.name,
        role=target.role,
        organization_id=target.institution_id,
        organization_name=org.name if org else None,
        is_active=target.is_active,
        permissions=perms
    )

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_role(["SUPER_ADMIN"]))
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own Super Admin account.")
        
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
        
    email = target.email
    db.delete(target)
    db.commit()
    
    deps.log_audit_trail(
        db=db,
        action="USER_DELETED",
        resource="USER",
        resource_id=str(user_id),
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"deleted_email": email}
    )
    
    return {"status": "SUCCESS", "message": f"User {email} has been deleted."}
