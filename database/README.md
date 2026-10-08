# CampusFind Database

Database/storage setup only. Existing `frontend/`, `backend/`, and `ai/` directory structures are preserved.

1. Create a Supabase project.
2. Run `schema.sql` and `storage.sql` in Supabase SQL Editor.
3. Set the backend environment variables from `.env.example`.
4. The existing `/users/register`, `/users/login`, and `/users/me` APIs continue to work unchanged, using PostgreSQL through `DATABASE_URL`.
5. Uploaded images are kept in Supabase Storage and their persistent URL is stored in `items.image_url`.

Never commit the Supabase service-role key.
