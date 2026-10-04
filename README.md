# SellerZone

SellerZone is a Flask + MongoDB online marketplace with a browser frontend and admin panel.

## Deploy to Railway

1. Push this folder to a GitHub repository.
2. In Railway, create a new project and choose **Deploy from GitHub Repo**.
3. Railway will use the included `Dockerfile` and `railway.json`.
4. Add these Railway Variables:

```text
MONGO_URI=<your MongoDB connection string>
DB_NAME=sellerzone
JWT_SECRET=<long random secret>
ADMIN_PASSWORD=<strong admin password>
ADMIN_SECRET=<long random admin secret>
```

5. Deploy. Railway injects `PORT`; the container listens on it automatically.
6. Generate a Railway public domain from the service's Networking settings.
7. To use a custom domain such as `sellerzone.example`, add it in Railway Networking and configure the DNS records Railway provides.

## MongoDB

This application uses MongoDB for users, products, carts, orders, wallet records, messages, invite codes, and settings. A persistent MongoDB service is required; do not use `mongodb://localhost` on Railway.

Railway also provides a MongoDB template if you want the database managed inside Railway.

## Seed demo products

After the first deployment, run the seed script once from an environment that can reach the same MongoDB database:

```bash
python backend/seed.py
```

The seed script skips seeding if products already exist.

## URLs

- Store: `/`
- Admin panel: `/admin`
- Health check: `/api/health`

## Security

Never commit `backend/.env` or real Railway secrets. The original uploaded archive contained local development credentials; this deployment package intentionally excludes that file. Change any credentials that may have been exposed previously.


### Product images
Product images from remote HTTPS URLs are served through `/api/image` so Railway deployments can display them reliably. Images that fail to load fall back gracefully.
