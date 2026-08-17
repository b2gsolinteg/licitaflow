DO $$
BEGIN
    IF to_regclass('users') IS NULL OR to_regclass('assisted_requests') IS NULL THEN
        RAISE EXCEPTION 'users e assisted_requests devem existir antes de 0002_support_messages.sql';
    END IF;

    CREATE TABLE IF NOT EXISTS assisted_request_messages(
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL REFERENCES assisted_requests(id) ON DELETE CASCADE,
        sender_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        sender_role TEXT NOT NULL,
        body TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        read_at TIMESTAMPTZ
    );

    CREATE INDEX IF NOT EXISTS idx_assisted_request_messages_request
        ON assisted_request_messages(request_id, created_at);

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname='ck_assisted_request_messages_sender_role'
          AND conrelid='assisted_request_messages'::regclass
    ) THEN
        ALTER TABLE assisted_request_messages
        ADD CONSTRAINT ck_assisted_request_messages_sender_role
        CHECK (sender_role IN ('user','admin'));
    END IF;
END
$$;
