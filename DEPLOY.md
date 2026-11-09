# Deployment (free/demo setup)

The API can use SQLite locally and PostgreSQL in a hosted deployment. Render's
free PostgreSQL databases are temporary, so this service is configured to take
an external PostgreSQL connection string instead of creating a Render database.

## Render + free Neon PostgreSQL

1. Create a free PostgreSQL project in Neon and copy its pooled or direct
   connection string. Keep the connection string private.
2. Push/merge the `copilot/fix-python-312-and-tests` branch into `main` so the
   deployment files are present on the branch Render will deploy.
3. In Render, create a Blueprint from this repository and select the `main`
   branch. Render reads `render.yaml` and creates the free Docker web service.
4. When prompted, set `DATABASE_URL` to the Neon connection string in Render's
   environment settings. The app accepts `postgres://` and `postgresql://`
   URLs and uses the psycopg 3 driver.
5. Deploy, then check `https://<your-render-service>.onrender.com/health` and
   `/docs`.

Do not commit the database URL or any provider API keys. For a demo, the mock
provider works without API keys. Add real provider keys only as Render secret
environment variables.

The Render free web service may spin down after inactivity. Free database
providers can impose their own storage, compute, inactivity, or retention
limits; check the selected provider's current plan before relying on it for
important data. Back up data you need to keep.

## Local PostgreSQL (optional)

Set `DATABASE_URL` to a PostgreSQL connection string before starting the app.
If it is unset, the app continues to use the local SQLite database.
