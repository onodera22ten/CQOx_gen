"""
Row-Level Security (RLS) for Multi-Tenancy

PostgreSQLのRow Level Securityを使用したマルチテナント実装
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger


class RLSManager:
    """
    Row-Level Security Manager
    
    **機能**:
    - Tenant isolationをデータベースレベルで強制
    - PostgreSQL RLSを使用
    - アプリケーションコードのバグによるデータ漏洩を防止
    """
    
    @staticmethod
    async def enable_rls(session: AsyncSession, table_name: str):
        """
        テーブルにRLSを有効化
        
        Args:
            session: Database session
            table_name: Table name
        """
        try:
            await session.execute(text(f"""
                ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
            """))
            await session.commit()
            logger.info(f"RLS enabled for table: {table_name}")
        except Exception as e:
            logger.error(f"Failed to enable RLS for {table_name}: {e}")
            await session.rollback()
            raise
    
    @staticmethod
    async def create_tenant_policy(session: AsyncSession, 
                                   table_name: str,
                                   tenant_col: str = "tenant_id"):
        """
        Tenant isolation policyを作成
        
        **Policy**:
        - SELECT: current_setting('app.current_tenant')に一致する行のみ
        - INSERT/UPDATE/DELETE: 同様に制限
        
        Args:
            session: Database session
            table_name: Table name
            tenant_col: Tenant ID column name
        """
        policy_name = f"{table_name}_tenant_isolation"
        
        try:
            # Drop existing policy if exists
            await session.execute(text(f"""
                DROP POLICY IF EXISTS {policy_name} ON {table_name};
            """))
            
            # Create tenant isolation policy
            await session.execute(text(f"""
                CREATE POLICY {policy_name} ON {table_name}
                USING ({tenant_col} = current_setting('app.current_tenant')::text);
            """))
            
            await session.commit()
            logger.info(f"Tenant isolation policy created for: {table_name}")
        except Exception as e:
            logger.error(f"Failed to create policy for {table_name}: {e}")
            await session.rollback()
            raise
    
    @staticmethod
    async def set_current_tenant(session: AsyncSession, tenant_id: str):
        """
        現在のテナントをセッションに設定
        
        Args:
            session: Database session
            tenant_id: Tenant ID
        """
        try:
            await session.execute(text(f"""
                SET LOCAL app.current_tenant = '{tenant_id}';
            """))
            logger.debug(f"Current tenant set to: {tenant_id}")
        except Exception as e:
            logger.error(f"Failed to set current tenant: {e}")
            raise
    
    @staticmethod
    async def clear_current_tenant(session: AsyncSession):
        """現在のテナント設定をクリア"""
        try:
            await session.execute(text("""
                RESET app.current_tenant;
            """))
        except Exception as e:
            logger.warning(f"Failed to clear current tenant: {e}")


async def setup_rls_for_all_tables(session: AsyncSession):
    """
    全テーブルにRLSを設定（初期化時に1回実行）
    
    Args:
        session: Database session
    """
    tables = [
        "datasets",
        "policies",
        "decisions",
        "analysis_runs",
        "column_mapping_profiles"
    ]
    
    rls_manager = RLSManager()
    
    for table in tables:
        try:
            await rls_manager.enable_rls(session, table)
            await rls_manager.create_tenant_policy(session, table)
        except Exception as e:
            logger.error(f"Failed to setup RLS for {table}: {e}")
    
    logger.info("RLS setup completed for all tables")


# Dependency for FastAPI
async def enforce_tenant_isolation(session: AsyncSession, tenant_id: Optional[str]):
    """
    FastAPI dependency to enforce tenant isolation
    
    Usage:
        @router.get("/data")
        async def get_data(
            db: AsyncSession = Depends(get_db),
            current_user = Depends(get_current_user)
        ):
            await enforce_tenant_isolation(db, current_user.get("tenant_id"))
            # Now all queries are automatically filtered by tenant_id
    """
    if tenant_id:
        await RLSManager.set_current_tenant(session, tenant_id)

