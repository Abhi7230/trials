"""Bill splitting with largest remainder allocation."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Any


def allocate_by_largest_remainder(total_cents: int, weights: list[int]) -> list[int]:
    """
    Allocate total across weights using largest remainder method.
    
    Ties go to earlier indices.
    """
    if not weights or sum(weights) == 0:
        return [0] * len(weights)

    total_weight = sum(weights)
    
    # Calculate exact shares
    exact_shares = [Decimal(total_cents) * Decimal(w) / Decimal(total_weight) for w in weights]
    
    # Get integer parts and remainders
    integer_parts = [int(share) for share in exact_shares]
    remainders = [share - int(share) for share in exact_shares]
    
    # Distribute remaining cents by largest remainder (ties to earlier index)
    allocated_sum = sum(integer_parts)
    remaining = total_cents - allocated_sum
    
    # Sort by remainder (descending), but keep original indices
    # Ties are broken by index (earlier first) due to stable sort
    indexed_remainders = list(enumerate(remainders))
    indexed_remainders.sort(key=lambda x: x[1], reverse=True)
    
    # Allocate remaining cents
    result = integer_parts[:]
    for i in range(remaining):
        idx = indexed_remainders[i][0]
        result[idx] += 1
    
    return result


class BillSplitter:
    """Split bills with tax and tip."""

    def split_bill(
        self,
        payer: str,
        participants: list[str],
        items: list[dict[str, Any]],
        tax_rate: float,
        tip_rate: float,
        tip_base: str,
    ) -> dict[str, Any]:
        """
        Split a bill among participants.
        
        Returns breakdown and list of request IDs.
        """
        if len(participants) > 100:
            raise ValueError("Too many participants")

        # Calculate item totals per person and shared items
        participant_items: dict[str, int] = {p: 0 for p in participants}
        shared_total = 0

        for item in items:
            amount = item["amount_cents"]
            if item.get("owner"):
                if item["owner"] in participant_items:
                    participant_items[item["owner"]] += amount
                else:
                    raise ValueError(f"Unknown item owner: {item['owner']}")
            else:
                shared_total += amount

        # Split shared items equally
        shared_per_person = allocate_by_largest_remainder(shared_total, [1] * len(participants))
        
        for i, participant in enumerate(participants):
            participant_items[participant] += shared_per_person[i]

        # Calculate pre-tax subtotal
        subtotal = sum(participant_items.values())

        # Calculate tax (rounded with ROUND_HALF_UP)
        tax_decimal = Decimal(str(subtotal)) * Decimal(str(tax_rate))
        tax_cents = int(tax_decimal.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

        # Calculate tip (rounded with ROUND_HALF_UP)
        tip_base_amount = subtotal if tip_base == "pre_tax" else subtotal + tax_cents
        tip_decimal = Decimal(str(tip_base_amount)) * Decimal(str(tip_rate))
        tip_cents = int(tip_decimal.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

        # Allocate tax and tip by largest remainder
        weights = [participant_items[p] for p in participants]
        tax_allocations = allocate_by_largest_remainder(tax_cents, weights)
        tip_allocations = allocate_by_largest_remainder(tip_cents, weights)

        # Build shares
        shares = []
        for i, participant in enumerate(participants):
            share = {
                "participant": participant,
                "items_cents": participant_items[participant] - shared_per_person[i],
                "shared_cents": shared_per_person[i],
                "subtotal_cents": participant_items[participant],
                "tax_cents": tax_allocations[i],
                "tip_cents": tip_allocations[i],
                "total_cents": participant_items[participant] + tax_allocations[i] + tip_allocations[i],
            }
            shares.append(share)

        grand_total = subtotal + tax_cents + tip_cents

        return {
            "payer": payer,
            "items_total_cents": subtotal,
            "tax_cents": tax_cents,
            "tip_cents": tip_cents,
            "grand_total_cents": grand_total,
            "shares": shares,
        }
