#!/usr/bin/env python3
"""
Test script to verify all portal pages are accessible
"""

import os
import requests
from urllib.parse import urljoin

# Base URL for testing
BASE_URL = "http://localhost:8080"

# List of all portal pages to test
PORTAL_PAGES = [
    "/portal/index.html",
    "/portal/water/index.html",
    "/portal/settlement.html",
    "/portal/payment.html",
    "/portal/register.html",
    "/portal/invoice-apply.html",
    "/portal/invoices.html",
    "/portal/orders.html",
    "/portal/change-password.html",
    "/portal/membership.html",
    "/portal/membership-plans.html",
    # Admin pages
    "/portal/admin/index.html",
    "/portal/admin/login.html",
    "/portal/admin/users.html",
    "/portal/admin/offices.html",
    "/portal/admin/settlements.html",
    "/portal/admin/login-logs.html",
    "/portal/admin/membership-plans.html",
    # Water admin pages
    "/portal/admin/water/dashboard.html",
    "/portal/admin/water/pickups.html",
    "/portal/admin/water/products.html",
    "/portal/admin/water/accounts.html",
    "/portal/admin/water/settlement_v3.html",
    "/portal/admin/water/monthly_settlement.html",
    # Meeting admin pages
    "/portal/admin/meeting/rooms.html",
    "/portal/admin/meeting/bookings.html",
    "/portal/admin/meeting/approvals.html",
]


def test_page_accessibility():
    """Test that all portal pages are accessible"""
    failed_pages = []

    for page in PORTAL_PAGES:
        try:
            url = urljoin(BASE_URL, page)
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                print(f"✅ {page} - OK")
            else:
                print(f"❌ {page} - Status {response.status_code}")
                failed_pages.append(page)

        except Exception as e:
            print(f"❌ {page} - Error: {str(e)}")
            failed_pages.append(page)

    if failed_pages:
        print(f"\n❌ {len(failed_pages)} pages failed:")
        for page in failed_pages:
            print(f"  - {page}")
        return False
    else:
        print(f"\n✅ All {len(PORTAL_PAGES)} pages are accessible!")
        return True


if __name__ == "__main__":
    test_page_accessibility()
