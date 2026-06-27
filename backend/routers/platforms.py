from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone

from backend.database import get_db
from backend.models.user import User
from backend.models.platform import PlatformAccount, PlatformEnum
from backend.auth import get_current_user
from backend.scrapers.codeforces import fetch_user_info, fetch_user_submissions, CodeforcesError
from backend.services.sync_service import sync_submissions

router = APIRouter(prefix="/platforms", tags=["platforms"])


# --- Schemas -----------------------------------------------------------------

class ConnectCodeforcesRequest(BaseModel):
    handle: str


class ConnectLeetCodeRequest(BaseModel):
    username: str
    session_cookie: str  # LEETCODE_SESSION cookie value


class ConnectCodeChefRequest(BaseModel):
    username: str


class PlatformStatusResponse(BaseModel):
    platform: str
    handle: str
    last_synced_at: str | None


class SyncResultResponse(BaseModel):
    platform: str
    handle: str
    new_submissions: int
    new_problems: int
    skipped: int
    synced_at: str


# --- Endpoints ---------------------------------------------------------------

@router.post("/connect/codeforces")
async def connect_codeforces(
    payload: ConnectCodeforcesRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link a Codeforces handle and trigger an initial sync."""
    # Validate handle exists on CF
    try:
        cf_info = await fetch_user_info(payload.handle)
    except CodeforcesError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Upsert platform account
    result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.user_id == current_user.id,
            PlatformAccount.platform == PlatformEnum.codeforces,
        )
    )
    account = result.scalar_one_or_none()

    if account:
        account.handle = payload.handle
    else:
        account = PlatformAccount(
            user_id=current_user.id,
            platform=PlatformEnum.codeforces,
            handle=payload.handle,
        )
        db.add(account)

    await db.commit()

    # Trigger background sync
    background_tasks.add_task(
        _background_sync_codeforces, current_user.id, payload.handle
    )

    return {
        "message": f"Connected Codeforces handle '{payload.handle}'. Sync started in background.",
        "cf_rating": cf_info.get("rating"),
        "cf_rank": cf_info.get("rank"),
    }


@router.post("/connect/leetcode")
async def connect_leetcode(
    payload: ConnectLeetCodeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link a LeetCode account with session cookie and trigger initial sync."""
    result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.user_id == current_user.id,
            PlatformAccount.platform == PlatformEnum.leetcode,
        )
    )
    account = result.scalar_one_or_none()

    if account:
        account.handle = payload.username
        account.cookies_json = payload.session_cookie
    else:
        account = PlatformAccount(
            user_id=current_user.id,
            platform=PlatformEnum.leetcode,
            handle=payload.username,
            cookies_json=payload.session_cookie,
        )
        db.add(account)

    await db.commit()

    # Trigger background sync
    background_tasks.add_task(
        _background_sync_leetcode, current_user.id, payload.username, payload.session_cookie
    )

    return {
        "message": f"Connected LeetCode username '{payload.username}'. Sync started in background.",
    }


@router.post("/connect/codechef")
async def connect_codechef(
    payload: ConnectCodeChefRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link a CodeChef account and trigger an initial sync."""
    from backend.scrapers.codechef import fetch_user_info as cc_fetch_user
    try:
        await cc_fetch_user(payload.username)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CodeChef user not found: {e}")

    result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.user_id == current_user.id,
            PlatformAccount.platform == PlatformEnum.codechef,
        )
    )
    account = result.scalar_one_or_none()

    if account:
        account.handle = payload.username
    else:
        account = PlatformAccount(
            user_id=current_user.id,
            platform=PlatformEnum.codechef,
            handle=payload.username,
        )
        db.add(account)

    await db.commit()

    background_tasks.add_task(
        _background_sync_codechef, current_user.id, payload.username
    )

    return {
        "message": f"Connected CodeChef username '{payload.username}'. Sync started in background.",
    }


@router.post("/sync/{platform}", response_model=SyncResultResponse)
async def sync_platform(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a sync for a platform."""
    result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.user_id == current_user.id,
            PlatformAccount.platform == platform,
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail=f"No {platform} account connected")

    if platform == "codeforces":
        try:
            raw = await fetch_user_submissions(account.handle)
        except CodeforcesError as e:
            raise HTTPException(status_code=502, detail=str(e))

        summary = await sync_submissions(db, current_user.id, raw)
        account.last_synced_at = datetime.now(timezone.utc)
        await db.commit()

        return SyncResultResponse(
            platform="codeforces",
            handle=account.handle,
            new_submissions=summary["new_submissions"],
            new_problems=summary["new_problems"],
            skipped=summary["skipped"],
            synced_at=account.last_synced_at.isoformat(),
        )

    elif platform == "leetcode":
        if not account.cookies_json:
            raise HTTPException(status_code=400, detail="No LeetCode session cookie stored. Re-connect your account.")

        from backend.scrapers.leetcode import fetch_leetcode_submissions
        try:
            raw = await fetch_leetcode_submissions(account.handle, account.cookies_json)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LeetCode scrape failed: {e}")

        summary = await sync_submissions(db, current_user.id, raw)
        account.last_synced_at = datetime.now(timezone.utc)
        await db.commit()

        return SyncResultResponse(
            platform="leetcode",
            handle=account.handle,
            new_submissions=summary["new_submissions"],
            new_problems=summary["new_problems"],
            skipped=summary["skipped"],
            synced_at=account.last_synced_at.isoformat(),
        )

    else:
        raise HTTPException(status_code=400, detail=f"Sync for {platform} not yet implemented")


@router.get("/status", response_model=list[PlatformStatusResponse])
async def platforms_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get connection status for all platforms."""
    result = await db.execute(
        select(PlatformAccount).where(PlatformAccount.user_id == current_user.id)
    )
    accounts = result.scalars().all()

    return [
        PlatformStatusResponse(
            platform=acc.platform,
            handle=acc.handle,
            last_synced_at=acc.last_synced_at.isoformat() if acc.last_synced_at else None,
        )
        for acc in accounts
    ]


# --- Background helpers ------------------------------------------------------

async def _background_sync_codeforces(user_id: int, handle: str):
    """Background task for initial CF sync."""
    from backend.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            raw = await fetch_user_submissions(handle)
            await sync_submissions(db, user_id, raw)
            await db.execute(
                update(PlatformAccount)
                .where(
                    PlatformAccount.user_id == user_id,
                    PlatformAccount.platform == PlatformEnum.codeforces,
                )
                .values(last_synced_at=datetime.now(timezone.utc))
            )
            await db.commit()
        except Exception as e:
            print(f"[ERROR] CF background sync failed for user {user_id}: {e}")


async def _background_sync_leetcode(user_id: int, username: str, session_cookie: str):
    """Background task for initial LeetCode sync."""
    from backend.database import AsyncSessionLocal
    from backend.scrapers.leetcode import fetch_leetcode_submissions

    async with AsyncSessionLocal() as db:
        try:
            raw = await fetch_leetcode_submissions(username, session_cookie)
            if raw:
                await sync_submissions(db, user_id, raw)
            await db.execute(
                update(PlatformAccount)
                .where(
                    PlatformAccount.user_id == user_id,
                    PlatformAccount.platform == PlatformEnum.leetcode,
                )
                .values(last_synced_at=datetime.now(timezone.utc))
            )
            await db.commit()
            print(f"[OK] LC background sync done for user {user_id}: {len(raw)} submissions")
        except Exception as e:
            print(f"[ERROR] LC background sync failed for user {user_id}: {e}")


async def _background_sync_codechef(user_id: int, username: str):
    """Background task for initial CodeChef sync."""
    from backend.database import AsyncSessionLocal
    from backend.scrapers.codechef import fetch_submissions, fetch_problem_tags

    async with AsyncSessionLocal() as db:
        try:
            raw_subs = await fetch_submissions(username)

            # Enrich tags for each problem (sample first 20 to limit API calls)
            enriched = []
            seen = set()
            for s in raw_subs:
                pid = s["problem_id"]
                if pid not in seen:
                    seen.add(pid)
                    if len(seen) <= 20:
                        tags = await fetch_problem_tags(pid)
                        s["tags"] = tags
                enriched.append(s)

            if enriched:
                await sync_submissions(db, user_id, enriched)

            await db.execute(
                update(PlatformAccount)
                .where(
                    PlatformAccount.user_id == user_id,
                    PlatformAccount.platform == PlatformEnum.codechef,
                )
                .values(last_synced_at=datetime.now(timezone.utc))
            )
            await db.commit()
            print(f"[OK] CC background sync done for user {user_id}: {len(enriched)} submissions")
        except Exception as e:
            print(f"[ERROR] CC background sync failed for user {user_id}: {e}")
