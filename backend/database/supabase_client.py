from supabase import create_client, Client
import vars as vars

# Initialize Supabase client
supabase: Client = create_client(str(vars.supabase_url), str(vars.supabase_key))

def get_supabase_client() -> Client:
    """Get the Supabase client instance."""
    return supabase
