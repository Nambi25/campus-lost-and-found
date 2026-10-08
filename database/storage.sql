INSERT INTO storage.buckets (id, name, public) VALUES ('campusfind-images', 'campusfind-images', true) ON CONFLICT (id) DO UPDATE SET public = true;
DROP POLICY IF EXISTS "CampusFind public image read" ON storage.objects;
CREATE POLICY "CampusFind public image read" ON storage.objects FOR SELECT TO public USING (bucket_id = 'campusfind-images');
