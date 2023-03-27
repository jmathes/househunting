from util import ds


def explain(price=1457000., downpayment=1547000*.2, annual_interest=6.4, monthly_payment=8293., decrease_interest_to=None, decrease_after_years=0., monthly_insurance=510., monthly_tax=1238.):
    if decrease_interest_to is None:
        decrease_interest_to = annual_interest
    monthly_payment -= monthly_tax + monthly_insurance
    print(monthly_payment)
    monthly_interest = annual_interest / 1200
    remaining_loan = price - downpayment
    years_elapsed = 0
    principal_paid = 0
    interest_paid = 0
    month = 0
    while remaining_loan > 0:
        # print()
        # print(f"After {years_elapsed} years, {ds(principal_paid)} principal paid, {ds(interest_paid)} interest paid, {ds(principal_paid + interest_paid)} paid total, {ds(remaining_loan)} remaining")
        monthly_totals = "    "
        if years_elapsed == decrease_after_years:
            monthly_interest = decrease_interest_to / 1200
        # if years_elapsed == 5:
        #     remaining_loan -= 500000
        for month in range(12):
            this_month_interest = remaining_loan * monthly_interest
            this_month_principal = monthly_payment - this_month_interest
            interest_paid += this_month_interest
            principal_paid += this_month_principal
            remaining_loan -= this_month_principal
            monthly_totals += f"{ds(remaining_loan)}" + " " * (11 - len(ds(remaining_loan)))
            # print(monthly_totals)
            if remaining_loan < 0:
                break
        years_elapsed += 1

    print(
        f"After {years_elapsed} years {month} months, {ds(principal_paid)} principal paid, {ds(interest_paid)} interest paid, {ds(principal_paid + interest_paid)} paid total, {ds(remaining_loan)} remaining"
    )


explain(
    price=1400000,
    downpayment=1400000 * 0.2,
    # annual_interest=6.4,
    monthly_payment=9000,
    monthly_tax=1238 * .96,
    # monthly_insurance=510,
    # decrease_interest_to=4.4,
    # decrease_after_years=6,
)
