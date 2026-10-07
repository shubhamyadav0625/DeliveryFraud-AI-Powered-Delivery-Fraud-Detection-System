import random
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.order import Order, OrderStatus
from app.models.package import Package, PackingEvent
from app.schemas.packing import PackageWeightCreate, PackageResponse
from app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/packing", tags=["Warehouse & Packing Logistics"])

@router.post("/record-weight", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
def record_package_weight_and_scans(
    pkg_in: PackageWeightCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DELIVERY_PARTNER]))
):
    order = db.query(Order).filter(Order.id == pkg_in.order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    existing_pkg = db.query(Package).filter(Package.order_id == pkg_in.order_id).first()
    if existing_pkg:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Package weight already recorded for this order")

    total_expected_weight = sum(item.expected_weight_grams * item.quantity for item in order.items)
    package_barcode = f"PKG-{random.randint(100000, 999999)}"

    package = Package(
        order_id=order.id,
        package_barcode=package_barcode,
        total_expected_weight_grams=total_expected_weight,
        measured_weight_grams=pkg_in.measured_weight_grams,
        seal_intact=pkg_in.seal_intact
    )
    db.add(package)
    db.flush()

    for event in pkg_in.packing_events:
        pe = PackingEvent(
            package_id=package.id,
            sku=event.sku,
            scanned=event.scanned,
            station_id=event.station_id
        )
        db.add(pe)

    order.status = OrderStatus.PACKED
    db.commit()
    db.refresh(package)
    return package
