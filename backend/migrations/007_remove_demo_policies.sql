-- Remove legacy auto-seeded demo policies
DELETE FROM policies
WHERE name IN ('Email Campaign A', 'Multi-Channel B', 'Retention Offer C');
