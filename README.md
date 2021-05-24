# Business Variance Analysis Tool
A calculator that does variance analysis (the management accounting kind, not ANOVA) to explain the "variance" (difference) between two accounting periods.

Works on any data with rate and volume:
- **Rate** (e.g. average clicks per user, price per product)
- **Volume** (e.g. number of users, number of products sold).

## Examples
- A website might analyze total user time on site with these:
  - **Index**: Domain
  - **Index**: Subdomain
  - **Index**: Pages
  - **Volume**: Number of users
  - **Rate**: Average time on site per user
- A consumer goods company might analyze total revenue with these:
  - **Index**: Brand
  - **Index**: Subbrand
  - **Index**: SKU Name
  - **Volume**: Units sold
  - **Rate**: Price $ per unit

**Total value = ∑(rate x volume)**, in our examples it is:
- Total time on site (time on site per user * users)
- Total revenue (price per unit * units)

## What is this sorcery?
Variance analysis explains the difference in total value. It tries to answer this question:

*Did we have more/less total value:*
- Rate difference
  - (website example) because the **overall average time on site per user** went up/down?
  - (goods example) because the **overall average price per unit** went up/down?
- Volume difference
  - (website example) because the **number of total users on site** went up/down?
  - (goods example) because the **number of total units sold** went up/down?
- Mix difference (change in distribution)
  - (website example) because there is **more traffic to domains/subdomains/pages that, on average, keep users on site for longer/shorter**?
  - (goods example) because we sold **more units in brands/subbrands/SKUs that, on average, is more expensive / cheaper**?
