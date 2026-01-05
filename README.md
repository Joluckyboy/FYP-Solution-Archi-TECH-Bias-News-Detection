### 1. Environment Variables

Your `.env` file should contain these (the one Xinlin provided in telegram):

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_KEY`

and be placed in the `backend/` directory.

### 2. Docker Compose
```bash
docker-compose up --build
```

### 3. Accessing Database Endpoints
The API Docs can be accessed at:
http://127.0.0.1:8011/docs#/

I added a dummy entry into the news_data table for testing purposes.
You can test an endpoint such as `POST /database/check_exists/` using the Swagger UI or Postman.
In the body:
```json
{
  "url": "https://bbc.com/news/test-123"
}
```
It should return a `201 Created` response with content:
```json
{
  "exists": true
}
```

### Additional Notes
If you want to rebuild any service, you can run:
```bash
docker-compose up --build <service_name>
```

The following services PORTS:
- application: 8010
- database: 8011
- sentiment: 8012
- emotion: 8013
- propaganda: 8014
- scrapper: 8015
- fact-check: 8016
- telebot: 8020
