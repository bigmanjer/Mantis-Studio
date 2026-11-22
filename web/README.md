# MANTIS Studio — Web

The subscription web version of MANTIS Studio: Next.js + Supabase (accounts, database) + Stripe (billing), hosted on Vercel.

- **Setup and deployment:** see [SETUP.md](SETUP.md)
- **Database schema:** [supabase/schema.sql](supabase/schema.sql)
- **Plans, prices and limits:** [src/lib/plans.ts](src/lib/plans.ts)

```bash
npm install
npm run dev      # http://localhost:3000
npm run build
npm run lint
```
