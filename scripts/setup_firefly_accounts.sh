#!/usr/bin/env bash
set -euo pipefail

TOKEN="${FIREFLY_TOKEN:?FIREFLY_TOKEN env var is not set}"

REMOTE_SCRIPT=$(cat << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

FIREFLY_URL="http://localhost:8080/api/v1"
TOKEN="${FIREFLY_TOKEN}"

declare -A ACCOUNT_TYPES
declare -A ACCOUNT_NUMBERS
declare -A ACCOUNT_LIABILITIES_TYPE

ACCOUNTS=(
    "Brukskonto"
    "Boligutgifter"
    "Egenkapital"
    "Fellesutgifter"
    "Bank Norwegian"
)

ACCOUNT_TYPES["Brukskonto"]="asset"
ACCOUNT_TYPES["Boligutgifter"]="asset"
ACCOUNT_TYPES["Egenkapital"]="asset"
ACCOUNT_TYPES["Fellesutgifter"]="asset"
ACCOUNT_TYPES["Bank Norwegian"]="liabilities"

ACCOUNT_NUMBERS["Brukskonto"]="98660504184"
ACCOUNT_NUMBERS["Boligutgifter"]="18136780340"
ACCOUNT_NUMBERS["Egenkapital"]="18135872926"
ACCOUNT_NUMBERS["Fellesutgifter"]="18135655372"
ACCOUNT_NUMBERS["Bank Norwegian"]=""

ACCOUNT_LIABILITIES_TYPE["Bank Norwegian"]="debt"

echo "Fetching existing Firefly III accounts..."

EXISTING_NAMES=$(curl -sf \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Accept: application/json" \
    "${FIREFLY_URL}/accounts?type=asset&limit=100" \
    | jq -r '.data[].attributes.name' || true)

LIABILITIES=$(curl -sf \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Accept: application/json" \
    "${FIREFLY_URL}/accounts?type=liabilities&limit=100" \
    | jq -r '.data[].attributes.name' || true)

EXISTING_NAMES="${EXISTING_NAMES}"$'\n'"${LIABILITIES}"

echo ""
for NAME in "${ACCOUNTS[@]}"; do
    TYPE="${ACCOUNT_TYPES[$NAME]}"
    ACCOUNT_NUMBER="${ACCOUNT_NUMBERS[$NAME]}"

    if echo "${EXISTING_NAMES}" | grep -qx "${NAME}"; then
        echo "[SKIP]    ${NAME} (already exists)"
        continue
    fi

    PAYLOAD=$(jq -cn \
        --arg name "${NAME}" \
        --arg type "${TYPE}" \
        --arg currency "NOK" \
        --arg account_number "${ACCOUNT_NUMBER}" \
        '{
            name: $name,
            type: $type,
            currency_code: $currency,
            account_number: (if $account_number != "" then $account_number else null end),
            account_role: (if $type == "asset" then "defaultAsset" else null end),
            active: true
        } | with_entries(select(.value != null))')

    if [[ "${TYPE}" == "liabilities" ]]; then
        LIABILITY_TYPE="${ACCOUNT_LIABILITIES_TYPE[$NAME]}"
        PAYLOAD=$(echo "${PAYLOAD}" | jq -c \
            --arg lt "${LIABILITY_TYPE}" \
            '. + {liability_type: $lt, liability_direction: "debit"}')
    fi

    PAYLOAD_FILE=$(mktemp)
    echo "${PAYLOAD}" > "${PAYLOAD_FILE}"

    RESPONSE=$(curl -sf \
        -X POST \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Accept: application/json" \
        -H "Content-Type: application/json" \
        -d "@${PAYLOAD_FILE}" \
        "${FIREFLY_URL}/accounts")

    rm -f "${PAYLOAD_FILE}"

    CREATED_NAME=$(echo "${RESPONSE}" | jq -r '.data.attributes.name')
    echo "[CREATED] ${CREATED_NAME}"
done

echo ""
echo "Done."
SCRIPT
)

TMPFILE=$(mktemp)
echo "${REMOTE_SCRIPT}" > "${TMPFILE}"
scp -q "${TMPFILE}" firefly:/tmp/setup_firefly_accounts.sh
rm -f "${TMPFILE}"
ESCAPED_TOKEN=$(printf '%q' "${TOKEN}")
ssh firefly "FIREFLY_TOKEN=${ESCAPED_TOKEN} bash /tmp/setup_firefly_accounts.sh"
