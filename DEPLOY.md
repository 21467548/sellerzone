# SellerZone — GitHub + Railway Deployment

## 1. GitHub

Create a new GitHub repository, for example `sellerzone`, then upload the contents of this folder to the repository root.

The repository should contain `Dockerfile`, `railway.json`, `requirements.txt`, `backend/`, and `frontend/` at the top level.

## 2. MongoDB

SellerZone requires MongoDB. Create a persistent MongoDB database and copy its connection string.

If using a MongoDB service inside Railway, use the connection string supplied by that service. Do not use `mongodb://localhost:27017/` on Railway.

## 3. Railway

In Railway:

1. Create a new project.
2. Choose **Deploy from GitHub Repo**.
3. Select the `sellerzone` repository.
4. Railway will detect the included Dockerfile/configuration.
5. Add these service variables before or after the first deploy:

```text
MONGO_URI=<MongoDB connection string>
DB_NAME=sellerzone
JWT_SECRET=<long random secret>
ADMIN_PASSWORD=<strong admin password>
ADMIN_SECRET=<different long random secret>
```

6. Deploy the service.
7. Railway should use `/api/health` as the health check from `railway.json`.
8. Open **Settings → Networking → Generate Domain** to create the initial Railway URL.

## 4. Custom SellerZone domain

The code cannot register a real internet domain for you. If you own a domain such as `sellerzone.com`, add that custom domain in Railway Networking and then create the DNS record Railway shows you at your domain registrar.

## 5. Seed products

After the application is connected to the correct MongoDB database, run `python backend/seed.py` once from an environment that can reach the database. It will not duplicate products if products already exist.

## 6. URLs after deployment

- Store: `/`
- Admin: `/admin`
- Health: `/api/health`

## 7. Admin

Use the `ADMIN_PASSWORD` Railway variable to sign in at `/admin`. Do not rely on the development fallback password.

## Important

The original archive included a local `backend/.env` containing development credentials. It is intentionally excluded from this package. Because those credentials were present in the original archive, rotate/change them if they were used anywhere outside your private development machine.
