from django.core.management.base import BaseCommand
from django.db import connection, transaction

from core.models import FeePayment


class Command(BaseCommand):
    help = "Regenerate sequential receipt numbers for all payments based on payment date"

    def handle(self, *args, **options):
        # Get all payments ordered by payment_date (oldest first)
        payments = list(FeePayment.objects.all().order_by("payment_date", "created_at"))

        self.stdout.write(self.style.WARNING(f"Found {len(payments)} receipts to regenerate"))

        with transaction.atomic():
            # Use raw SQL to bypass unique constraint - update to temporary values first
            with connection.cursor() as cursor:
                for index, payment in enumerate(payments, start=1):
                    temp_receipt_no = f"TEMP-{index:06d}"
                    cursor.execute(
                        "UPDATE core_feepayment SET receipt_no = %s WHERE id = %s", [temp_receipt_no, payment.id]
                    )

            # Now update with actual sequential numbers
            for index, payment in enumerate(payments, start=1):
                temp_receipt_no = f"TEMP-{index:06d}"
                final_receipt_no = f"RCP-{index:06d}"
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE core_feepayment SET receipt_no = %s WHERE receipt_no = %s",
                        [final_receipt_no, temp_receipt_no],
                    )
                self.stdout.write(f"Updated: {temp_receipt_no} → {final_receipt_no}")

        self.stdout.write(self.style.SUCCESS(f"Successfully regenerated {len(payments)} receipt numbers"))
