#!/usr/bin/env bash
# Bring up a local WordPress + WooCommerce store for the live demo.
set -euo pipefail
cd "$(dirname "$0")"

WP="docker compose run --rm -T wpcli wp"

echo "[1/5] starting db + wordpress ..."
docker compose up -d db wordpress

echo "[2/5] waiting for WordPress to be ready ..."
for _ in $(seq 1 60); do
  if $WP core is-installed >/dev/null 2>&1 || $WP db check >/dev/null 2>&1; then
    break
  fi
  sleep 3
done

echo "[3/5] installing WordPress ..."
$WP core install \
  --url="http://localhost:8080" \
  --title="Agent Studio Demo Store" \
  --admin_user=admin \
  --admin_password=admin \
  --admin_email=admin@example.com \
  --skip-email || true

echo "[4/5] installing & activating WooCommerce ..."
$WP plugin install woocommerce --activate
$WP option update woocommerce_currency "INR" || true
$WP option update woocommerce_store_city "Bangalore" || true

echo "[5/5] done."
cat <<'EOF'

Next steps:
  1. Open http://localhost:8080/wp-admin  (admin / admin)
  2. WooCommerce > Settings > Advanced > REST API > Add key
       - Permissions: Read/Write  (Write is only needed for seeding)
       - Copy the ck_... and cs_... values
  3. Seed sample data:
       WC_STORE_URL=http://localhost:8080 \
       WC_CONSUMER_KEY=ck_... WC_CONSUMER_SECRET=cs_... \
       python seed_data.py
  4. Run the live demo:
       WC_STORE_URL=http://localhost:8080 \
       WC_CONSUMER_KEY=ck_... WC_CONSUMER_SECRET=cs_... \
       python demo_live.py
EOF
