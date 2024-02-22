INSERT INTO public.users (display_name, handle, cognito_user_id)
VALUES
  ('Andrew Brown', 'andrewbrown' ,'MOCK'),
  ('Andrew Bayko', 'bayko' ,'MOCK'),
  ('John Doe', 'johndoe' ,'MOCK'),
  ('Jane Smith', 'janesmith' ,'MOCK');

INSERT INTO public.activities (user_uuid, message, expires_at)
VALUES
  (
    (SELECT uuid from public.users WHERE users.handle = 'andrewbrown' LIMIT 1),
    'This was imported as seed data!',
    current_timestamp + interval '10 day'
  ),
  (
    (SELECT uuid from public.users WHERE users.handle = 'bayko' LIMIT 1),
    'Another seed data entry',
    current_timestamp + interval '5 day'
  ),
  (
    (SELECT uuid from public.users WHERE users.handle = 'johndoe' LIMIT 1),
    'Seed data for John Doe',
    current_timestamp + interval '7 day'
  ),
  (
    (SELECT uuid from public.users WHERE users.handle = 'janesmith' LIMIT 1),
    'Seed data for Jane Smith',
    current_timestamp + interval '3 day'
  );
