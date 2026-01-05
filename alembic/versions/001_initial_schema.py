"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2025-12-30 17:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('api_key', sa.String(length=255), nullable=False),
        sa.Column('balance', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_email', 'users', ['email'], unique=False)
    op.create_index('idx_user_api_key', 'users', ['api_key'], unique=False)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_api_key'), 'users', ['api_key'], unique=True)

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('DEPOSIT', 'WITHDRAWAL', name='transactiontype'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'SUCCESS', 'FAILED', name='transactionstatus'), nullable=False, server_default='PENDING'),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('bank_reference', sa.String(length=255), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_transaction_user_id', 'transactions', ['user_id'], unique=False)
    op.create_index('idx_transaction_status', 'transactions', ['status'], unique=False)
    op.create_index('idx_transaction_created_at', 'transactions', ['created_at'], unique=False)
    op.create_index('idx_transaction_idempotency_key', 'transactions', ['idempotency_key'], unique=False)
    op.create_index('idx_transaction_user_status', 'transactions', ['user_id', 'status'], unique=False)
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    op.create_index(op.f('ix_transactions_bank_reference'), 'transactions', ['bank_reference'], unique=True)

    # Create idempotency_keys table
    op.create_table(
        'idempotency_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('response_status', sa.Integer(), nullable=False),
        sa.Column('response_body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_idempotency_keys_id'), 'idempotency_keys', ['id'], unique=False)
    op.create_index(op.f('ix_idempotency_keys_key'), 'idempotency_keys', ['key'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_idempotency_keys_key'), table_name='idempotency_keys')
    op.drop_index(op.f('ix_idempotency_keys_id'), table_name='idempotency_keys')
    op.drop_table('idempotency_keys')
    
    op.drop_index(op.f('ix_transactions_bank_reference'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_id'), table_name='transactions')
    op.drop_index('idx_transaction_user_status', table_name='transactions')
    op.drop_index('idx_transaction_idempotency_key', table_name='transactions')
    op.drop_index('idx_transaction_created_at', table_name='transactions')
    op.drop_index('idx_transaction_status', table_name='transactions')
    op.drop_index('idx_transaction_user_id', table_name='transactions')
    op.drop_table('transactions')
    
    op.drop_index(op.f('ix_users_api_key'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index('idx_user_api_key', table_name='users')
    op.drop_index('idx_user_email', table_name='users')
    op.drop_table('users')
    
    # Drop enums
    sa.Enum(name='transactionstatus').drop(op.get_bind())
    sa.Enum(name='transactiontype').drop(op.get_bind())
