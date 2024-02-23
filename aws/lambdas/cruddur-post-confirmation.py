import psycopg2
import os

def lambda_handler(event, _):
    user = event['request']['userAttributes']

    user_display_name  = user['name']
    user_email         = user['email']
    user_handle        = user['preferred_username']
    user_cognito_id    = user['sub']

    try:
      conn = psycopg2.connect(os.getenv('CONNECTION_URL'))
      with conn, conn.cursor() as cur:
        sql = """
        INSERT INTO public.users (display_name, email, handle, cognito_user_id) 
        VALUES(%s,%s,%s,%s)
        """
        params = [
          user_display_name,
          user_email,
          user_handle,
          user_cognito_id
        ]
        cur.execute(sql, params)

    except (Exception) as error:
      print(f"An error occurred: {error}")
    return event