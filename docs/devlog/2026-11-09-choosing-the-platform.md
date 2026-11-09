---
title: "Choosing the platform"
date: 2026-11-09
refs: [ADR-0001, ADR-0002, LV-006]
status: "Draft, edit in your own words before keeping"
---

## Problem
Leave balances lived in a Google Sheet. An employee who completed one year on 1 Nov 2026 received no annual leave because the formula depended on a Permanent Date field that was empty. The office also needs attendance, payroll, assets, renewals, IT and finance records, and the old ERP will be replaced.

## What I considered
Frappe/ERPNext, Odoo Community and Enterprise, a Laravel custom build, a .NET custom build and Spring Boot. I scored them on business fit, security, maintainability, data integrity, team skills, performance and cost.

## What I decided and why
Frappe HR + ERPNext with one custom app. Payroll, accounting and audit already exist and are tested; there are no per-user licence fees; multi-company is built in. I accepted learning Python and Frappe, and MariaDB instead of PostgreSQL.

I also decided the product must work for other companies: one site per customer and every rule as configuration.

## What I learned

## Next
Confirm the leave rules with HR, clean the Sheet, set up the development bench.
