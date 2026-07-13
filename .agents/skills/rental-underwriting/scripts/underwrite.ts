#!/usr/bin/env bun

type ModeName = "ltr" | "str";
type LegalStatus = "ALLOWED" | "BLOCKED" | "UNKNOWN";
type RevenueStatus = "VERIFIED" | "HYPOTHETICAL" | "UNAVAILABLE";
type RevenueSourceType = "airdna_pricelabs" | "comps" | "broker_opinion" | "estimate";

interface LoanInput {
  annual_interest_rate: number;
  amortization_years: number;
}

interface PurchaseInput {
  address_label: string;
  purchase_price: number;
  cash_closing_costs: number;
  capitalizable_closing_costs: number;
  down_payment: number;
  annual_appreciation_rate: number;
  selling_cost_rate: number;
  loan: LoanInput;
}

interface TaxInput {
  magi: number;
  federal_marginal_rate: number;
  federal_capital_gains_rate: number;
  federal_unrecaptured_1250_rate: number;
  state_marginal_rate: number;
  state_capital_gains_rate: number;
  active_participation_ltr: boolean;
  state_active_participation_ltr: boolean;
  material_participation_str: boolean;
  average_guest_stay_nights: number;
  rented_days: number;
  personal_use_days: number;
  land_value_share: number;
  cost_seg_share: number;
  cost_seg_recovery_years: number;
  bonus_depreciation_rate: number;
  bonus_eligibility_confirmed: boolean;
  state_bonus_conforms: boolean;
  state_str_nonpassive_treatment_confirmed: boolean;
  state_str_nonpassive: boolean;
  building_recovery_years_ltr: number;
  building_recovery_years_str: number;
  building_recovery_years_str_sensitivity: number[];
  at_risk_limit: number | null;
  release_suspended_losses_on_sale: boolean;
}

interface DecisionHurdles {
  minimum_dscr: number;
  minimum_after_tax_irr: number;
  minimum_year1_cash_on_cash: number;
}

interface LegalInput {
  status: LegalStatus;
  jurisdiction_evidence: string[];
  hoa_evidence: string[];
}

interface RevenueInput {
  status: RevenueStatus;
  annual_gross_revenue: number | null;
  adr: number | null;
  occupancy_rate: number | null;
  available_nights: number | null;
  source_type: RevenueSourceType | null;
  comps_count: number | null;
  notes: string | null;
}

interface ExpenseInput {
  property_tax: number;
  insurance: number;
  hoa: number;
  utilities: number;
  management_fee_rate: number;
  maintenance_rate: number;
  capex_reserve_rate: number;
  platform_fee_rate: number;
  cleaning_fee_rate: number;
  lodging_tax_rate: number;
  lodging_tax_per_night: number;
  fixed_other: number;
}

interface ModeInput {
  enabled: boolean;
  legal: LegalInput;
  revenue: RevenueInput;
  vacancy_rate: number;
  other_income: number;
  revenue_growth_rate: number;
  expense_growth_rate: number;
  expenses: ExpenseInput;
}

interface UnderwriteInput {
  as_of: string;
  label: string;
  hypothetical: boolean;
  hold_years: number;
  purchase: PurchaseInput;
  tax: TaxInput;
  decision_hurdles: DecisionHurdles;
  modes: Record<ModeName, ModeInput>;
}

interface MortgageYear {
  year: number;
  opening_balance: number;
  principal_paid: number;
  interest_paid: number;
  debt_service: number;
  ending_balance: number;
}

interface MortgageSchedule {
  principal: number;
  monthly_payment: number;
  years: MortgageYear[];
}

interface DepreciationYear {
  year: number;
  federal_bonus: number;
  federal_cost_seg: number;
  federal_building: number;
  federal_total: number;
  state_bonus: number;
  state_cost_seg: number;
  state_building: number;
  state_total: number;
}

interface DepreciationPlan {
  building_recovery_years: number;
  building_basis: number;
  cost_seg_basis: number;
  land_basis: number;
  years: DepreciationYear[];
  totals: {
    federal_bonus: number;
    federal_cost_seg: number;
    federal_building: number;
    federal_total: number;
    state_bonus: number;
    state_cost_seg: number;
    state_building: number;
    state_total: number;
  };
}

interface OperatingBreakdown {
  fixed_expenses: number;
  variable_expenses: number;
  operating_expenses: number;
  effective_gross_income: number;
  noi: number;
  occupied_nights: number;
}

interface AnnualCashflowRow {
  year: number;
  gross_revenue: number;
  other_income: number;
  effective_gross_income: number;
  operating_expenses: number;
  noi: number;
  debt_service: number;
  interest_paid: number;
  principal_paid: number;
  pre_tax_cashflow: number;
  federal_taxable_income: number;
  federal_taxable_after_suspended: number;
  federal_suspended_used: number;
  state_taxable_income: number;
  state_taxable_after_suspended: number;
  state_suspended_used: number;
  federal_tax_due: number;
  federal_tax_savings: number;
  state_tax_due: number;
  state_tax_savings: number;
  after_tax_cashflow: number;
  federal_suspended_end: number;
  state_suspended_end: number;
}

interface ExitEstimate {
  estimated_sale_price: number;
  selling_costs: number;
  loan_payoff: number;
  amount_realized_net: number;
  adjusted_basis_federal: number;
  adjusted_basis_state: number;
  total_gain_federal: number;
  total_gain_state: number;
  state_taxable_gain: number;
  section_1245_recapture: number;
  unrecaptured_1250_gain: number;
  remaining_capital_gain: number;
  federal_tax_on_sale: number;
  state_tax_on_sale: number;
  suspended_loss_release_federal: number;
  suspended_loss_release_state: number;
  suspended_loss_release_tax_value: number;
  tax_due_after_release: number;
  before_tax_sale_proceeds: number;
  after_tax_sale_proceeds: number;
  estimate_note: string;
}

interface SensitivitySummary {
  building_recovery_years: number;
  year1_after_tax_cashflow: number;
  year1_federal_taxable_income: number;
  after_tax_irr: number | null;
  after_tax_irr_error: string | null;
}

interface ModeMetrics {
  cap_rate_year1: number | "[UNAVAILABLE]";
  dscr_year1: number | "[UNAVAILABLE]";
  cash_on_cash_year1: number | "[UNAVAILABLE]";
  break_even_str_occupancy: number | "[UNAVAILABLE]";
  after_tax_irr: number | null;
  after_tax_irr_error: string | null;
}

interface ModeResult {
  status: "ANALYZED" | "BLOCKED" | "DISABLED";
  decision: "BUY" | "PASS" | "BLOCKED" | "DISABLED";
  blocked_reasons: string[];
  warnings: string[];
  unavailable_fields: string[];
  legal_status: LegalStatus;
  revenue_status: RevenueStatus;
  metrics: ModeMetrics;
  annual_cashflows: AnnualCashflowRow[];
  depreciation: DepreciationPlan | "[UNAVAILABLE]";
  suspended_losses: {
    federal_end: number | "[UNAVAILABLE]";
    state_end: number | "[UNAVAILABLE]";
    release_assumed_on_sale: boolean;
  };
  exit_estimate: ExitEstimate | "[UNAVAILABLE]";
  recovery_year_sensitivity: SensitivitySummary[];
}

interface UnderwriteOutput {
  as_of: string;
  label: string;
  hypothetical: boolean;
  assumptions: string[];
  unavailable_fields: string[];
  warnings: string[];
  mode_results: Record<ModeName, ModeResult>;
  comparative_verdict: "BUY_LTR" | "BUY_STR" | "BUY_EITHER" | "PASS" | "BLOCKED";
}

const UNAVAILABLE = "[UNAVAILABLE]" as const;

function die(message: string): never {
  console.error(`error: ${message}`);
  process.exit(1);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function reqObject(parent: Record<string, unknown>, key: string, ctx: string): Record<string, unknown> {
  const value = parent[key];
  if (!isRecord(value)) die(`${ctx}.${key} must be an object`);
  return value;
}

function reqString(parent: Record<string, unknown>, key: string, ctx: string): string {
  const value = parent[key];
  if (typeof value !== "string" || !value.trim()) die(`${ctx}.${key} must be a non-empty string`);
  return value;
}

function reqBoolean(parent: Record<string, unknown>, key: string, ctx: string): boolean {
  const value = parent[key];
  if (typeof value !== "boolean") die(`${ctx}.${key} must be boolean`);
  return value;
}

function reqNumber(
  parent: Record<string, unknown>,
  key: string,
  ctx: string,
  min: number | null = null,
  max: number | null = null
): number {
  const value = parent[key];
  if (typeof value !== "number" || Number.isNaN(value) || !Number.isFinite(value)) {
    die(`${ctx}.${key} must be a finite number`);
  }
  if (min !== null && value < min) die(`${ctx}.${key} must be >= ${min}`);
  if (max !== null && value > max) die(`${ctx}.${key} must be <= ${max}`);
  return value;
}

function optNumber(
  parent: Record<string, unknown>,
  key: string,
  ctx: string,
  min: number | null = null,
  max: number | null = null
): number | null {
  const value = parent[key];
  if (value === undefined || value === null) return null;
  if (typeof value !== "number" || Number.isNaN(value) || !Number.isFinite(value)) {
    die(`${ctx}.${key} must be a finite number when provided`);
  }
  if (min !== null && value < min) die(`${ctx}.${key} must be >= ${min}`);
  if (max !== null && value > max) die(`${ctx}.${key} must be <= ${max}`);
  return value;
}

function optString(parent: Record<string, unknown>, key: string, ctx: string): string | null {
  const value = parent[key];
  if (value === undefined || value === null) return null;
  if (typeof value !== "string") die(`${ctx}.${key} must be string when provided`);
  return value;
}

function reqStringArray(parent: Record<string, unknown>, key: string, ctx: string): string[] {
  const value = parent[key];
  if (!Array.isArray(value)) die(`${ctx}.${key} must be an array of strings`);
  const out: string[] = [];
  for (let i = 0; i < value.length; i++) {
    const item = value[i];
    if (typeof item !== "string" || !item.trim()) die(`${ctx}.${key}[${i}] must be a non-empty string`);
    out.push(item);
  }
  return out;
}

function optNumberArray(
  parent: Record<string, unknown>,
  key: string,
  ctx: string,
  min: number | null = null,
  max: number | null = null
): number[] {
  const value = parent[key];
  if (value === undefined || value === null) return [];
  if (!Array.isArray(value)) die(`${ctx}.${key} must be an array of numbers`);
  const out: number[] = [];
  for (let i = 0; i < value.length; i++) {
    const item = value[i];
    if (typeof item !== "number" || Number.isNaN(item) || !Number.isFinite(item)) {
      die(`${ctx}.${key}[${i}] must be a finite number`);
    }
    if (min !== null && item < min) die(`${ctx}.${key}[${i}] must be >= ${min}`);
    if (max !== null && item > max) die(`${ctx}.${key}[${i}] must be <= ${max}`);
    out.push(item);
  }
  return out;
}

function reqEnum<T extends string>(
  parent: Record<string, unknown>,
  key: string,
  ctx: string,
  allowed: readonly T[]
): T {
  const value = parent[key];
  if (typeof value !== "string") die(`${ctx}.${key} must be one of ${allowed.join(", ")}`);
  if (!allowed.includes(value as T)) die(`${ctx}.${key} must be one of ${allowed.join(", ")}`);
  return value as T;
}

function parseRevenueInput(parent: Record<string, unknown>, ctx: string): RevenueInput {
  const status = reqEnum(parent, "status", ctx, ["VERIFIED", "HYPOTHETICAL", "UNAVAILABLE"] as const);
  const sourceType = parent["source_type"] === undefined || parent["source_type"] === null
    ? null
    : reqEnum(parent, "source_type", ctx, ["airdna_pricelabs", "comps", "broker_opinion", "estimate"] as const);
  return {
    status,
    annual_gross_revenue: optNumber(parent, "annual_gross_revenue", ctx, 0),
    adr: optNumber(parent, "adr", ctx, 0),
    occupancy_rate: optNumber(parent, "occupancy_rate", ctx, 0, 1),
    available_nights: optNumber(parent, "available_nights", ctx, 1),
    source_type: sourceType,
    comps_count: optNumber(parent, "comps_count", ctx, 0),
    notes: optString(parent, "notes", ctx),
  };
}

function parseModeInput(parent: Record<string, unknown>, mode: ModeName): ModeInput {
  const ctx = `modes.${mode}`;
  const legalObj = reqObject(parent, "legal", ctx);
  const revenueObj = reqObject(parent, "revenue", ctx);
  const expensesObj = reqObject(parent, "expenses", ctx);
  return {
    enabled: reqBoolean(parent, "enabled", ctx),
    legal: {
      status: reqEnum(legalObj, "status", `${ctx}.legal`, ["ALLOWED", "BLOCKED", "UNKNOWN"] as const),
      jurisdiction_evidence: reqStringArray(legalObj, "jurisdiction_evidence", `${ctx}.legal`),
      hoa_evidence: reqStringArray(legalObj, "hoa_evidence", `${ctx}.legal`),
    },
    revenue: parseRevenueInput(revenueObj, `${ctx}.revenue`),
    vacancy_rate: reqNumber(parent, "vacancy_rate", ctx, 0, 1),
    other_income: reqNumber(parent, "other_income", ctx, 0),
    revenue_growth_rate: reqNumber(parent, "revenue_growth_rate", ctx, -1, 2),
    expense_growth_rate: reqNumber(parent, "expense_growth_rate", ctx, -1, 2),
    expenses: {
      property_tax: reqNumber(expensesObj, "property_tax", `${ctx}.expenses`, 0),
      insurance: reqNumber(expensesObj, "insurance", `${ctx}.expenses`, 0),
      hoa: reqNumber(expensesObj, "hoa", `${ctx}.expenses`, 0),
      utilities: reqNumber(expensesObj, "utilities", `${ctx}.expenses`, 0),
      management_fee_rate: reqNumber(expensesObj, "management_fee_rate", `${ctx}.expenses`, 0, 1),
      maintenance_rate: reqNumber(expensesObj, "maintenance_rate", `${ctx}.expenses`, 0, 1),
      capex_reserve_rate: reqNumber(expensesObj, "capex_reserve_rate", `${ctx}.expenses`, 0, 1),
      platform_fee_rate: reqNumber(expensesObj, "platform_fee_rate", `${ctx}.expenses`, 0, 1),
      cleaning_fee_rate: reqNumber(expensesObj, "cleaning_fee_rate", `${ctx}.expenses`, 0, 1),
      lodging_tax_rate: reqNumber(expensesObj, "lodging_tax_rate", `${ctx}.expenses`, 0, 1),
      lodging_tax_per_night: reqNumber(expensesObj, "lodging_tax_per_night", `${ctx}.expenses`, 0),
      fixed_other: reqNumber(expensesObj, "fixed_other", `${ctx}.expenses`, 0),
    },
  };
}

function parseInput(raw: unknown): UnderwriteInput {
  if (!isRecord(raw)) die("input JSON must be an object");
  const purchaseObj = reqObject(raw, "purchase", "root");
  const loanObj = reqObject(purchaseObj, "loan", "purchase");
  const taxObj = reqObject(raw, "tax", "root");
  const hurdleObj = reqObject(raw, "decision_hurdles", "root");
  const modesObj = reqObject(raw, "modes", "root");
  if ("closing_costs" in purchaseObj) {
    die(
      "purchase.closing_costs is deprecated; provide purchase.cash_closing_costs and purchase.capitalizable_closing_costs"
    );
  }

  const input: UnderwriteInput = {
    as_of: reqString(raw, "as_of", "root"),
    label: reqString(raw, "label", "root"),
    hypothetical: reqBoolean(raw, "hypothetical", "root"),
    hold_years: Math.trunc(reqNumber(raw, "hold_years", "root", 1, 50)),
    purchase: {
      address_label: reqString(purchaseObj, "address_label", "purchase"),
      purchase_price: reqNumber(purchaseObj, "purchase_price", "purchase", 1),
      cash_closing_costs: reqNumber(purchaseObj, "cash_closing_costs", "purchase", 0),
      capitalizable_closing_costs: reqNumber(purchaseObj, "capitalizable_closing_costs", "purchase", 0),
      down_payment: reqNumber(purchaseObj, "down_payment", "purchase", 0),
      annual_appreciation_rate: reqNumber(purchaseObj, "annual_appreciation_rate", "purchase", -1, 2),
      selling_cost_rate: reqNumber(purchaseObj, "selling_cost_rate", "purchase", 0, 1),
      loan: {
        annual_interest_rate: reqNumber(loanObj, "annual_interest_rate", "purchase.loan", 0, 1),
        amortization_years: Math.trunc(reqNumber(loanObj, "amortization_years", "purchase.loan", 1, 50)),
      },
    },
    tax: {
      magi: reqNumber(taxObj, "magi", "tax", 0),
      federal_marginal_rate: reqNumber(taxObj, "federal_marginal_rate", "tax", 0, 1),
      federal_capital_gains_rate: reqNumber(taxObj, "federal_capital_gains_rate", "tax", 0, 1),
      federal_unrecaptured_1250_rate: reqNumber(taxObj, "federal_unrecaptured_1250_rate", "tax", 0, 1),
      state_marginal_rate: reqNumber(taxObj, "state_marginal_rate", "tax", 0, 1),
      state_capital_gains_rate: reqNumber(taxObj, "state_capital_gains_rate", "tax", 0, 1),
      active_participation_ltr: reqBoolean(taxObj, "active_participation_ltr", "tax"),
      state_active_participation_ltr: reqBoolean(taxObj, "state_active_participation_ltr", "tax"),
      material_participation_str: reqBoolean(taxObj, "material_participation_str", "tax"),
      average_guest_stay_nights: reqNumber(taxObj, "average_guest_stay_nights", "tax", 0),
      rented_days: reqNumber(taxObj, "rented_days", "tax", 0, 366),
      personal_use_days: reqNumber(taxObj, "personal_use_days", "tax", 0, 366),
      land_value_share: reqNumber(taxObj, "land_value_share", "tax", 0, 1),
      cost_seg_share: reqNumber(taxObj, "cost_seg_share", "tax", 0, 1),
      cost_seg_recovery_years: reqNumber(taxObj, "cost_seg_recovery_years", "tax", 0.5, 50),
      bonus_depreciation_rate: reqNumber(taxObj, "bonus_depreciation_rate", "tax", 0, 1),
      bonus_eligibility_confirmed: reqBoolean(taxObj, "bonus_eligibility_confirmed", "tax"),
      state_bonus_conforms: reqBoolean(taxObj, "state_bonus_conforms", "tax"),
      state_str_nonpassive_treatment_confirmed: reqBoolean(
        taxObj,
        "state_str_nonpassive_treatment_confirmed",
        "tax"
      ),
      state_str_nonpassive: reqBoolean(taxObj, "state_str_nonpassive", "tax"),
      building_recovery_years_ltr: reqNumber(taxObj, "building_recovery_years_ltr", "tax", 1, 60),
      building_recovery_years_str: optNumber(taxObj, "building_recovery_years_str", "tax", 1, 60) ?? 0,
      building_recovery_years_str_sensitivity: optNumberArray(taxObj, "building_recovery_years_str_sensitivity", "tax", 1, 60),
      at_risk_limit: optNumber(taxObj, "at_risk_limit", "tax", 0),
      release_suspended_losses_on_sale: reqBoolean(taxObj, "release_suspended_losses_on_sale", "tax"),
    },
    decision_hurdles: {
      minimum_dscr: reqNumber(hurdleObj, "minimum_dscr", "decision_hurdles", 0),
      minimum_after_tax_irr: reqNumber(hurdleObj, "minimum_after_tax_irr", "decision_hurdles", -0.99, 10),
      minimum_year1_cash_on_cash: reqNumber(hurdleObj, "minimum_year1_cash_on_cash", "decision_hurdles", -1, 10),
    },
    modes: {
      ltr: parseModeInput(reqObject(modesObj, "ltr", "modes"), "ltr"),
      str: parseModeInput(reqObject(modesObj, "str", "modes"), "str"),
    },
  };

  if (input.purchase.down_payment > input.purchase.purchase_price) {
    die("purchase.down_payment cannot exceed purchase_price");
  }
  if (input.purchase.capitalizable_closing_costs > input.purchase.cash_closing_costs) {
    die("purchase.capitalizable_closing_costs cannot exceed purchase.cash_closing_costs");
  }
  if (input.tax.bonus_depreciation_rate > 0 && !input.tax.bonus_eligibility_confirmed) {
    die("tax.bonus_eligibility_confirmed must be true when bonus_depreciation_rate > 0");
  }
  if (input.tax.state_str_nonpassive && !input.tax.state_str_nonpassive_treatment_confirmed) {
    die(
      "tax.state_str_nonpassive cannot be true unless tax.state_str_nonpassive_treatment_confirmed is true"
    );
  }
  if (input.purchase.loan.amortization_years < input.hold_years) {
    // This is valid but unusual; no fatal error.
  }
  if (
    input.tax.building_recovery_years_str <= 0 &&
    input.tax.building_recovery_years_str_sensitivity.length === 0
  ) {
    die("tax.building_recovery_years_str or tax.building_recovery_years_str_sensitivity is required");
  }
  if (input.tax.building_recovery_years_str <= 0) {
    input.tax.building_recovery_years_str = input.tax.building_recovery_years_str_sensitivity[0];
  }

  return input;
}

function round(value: number, digits = 2): number {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function activeParticipationAllowance(magi: number): number {
  if (magi <= 100000) return 25000;
  if (magi >= 150000) return 0;
  return Math.max(0, 25000 - 0.5 * (magi - 100000));
}

function mortgageSchedule(
  principal: number,
  annualRate: number,
  amortizationYears: number,
  holdYears: number
): MortgageSchedule {
  if (principal < 0) die("loan principal cannot be negative");
  if (principal === 0) {
    const zeroYears: MortgageYear[] = [];
    for (let year = 1; year <= holdYears; year++) {
      zeroYears.push({
        year,
        opening_balance: 0,
        principal_paid: 0,
        interest_paid: 0,
        debt_service: 0,
        ending_balance: 0,
      });
    }
    return {
      principal: 0,
      monthly_payment: 0,
      years: zeroYears,
    };
  }

  const monthlyRate = annualRate / 12;
  const totalPayments = amortizationYears * 12;
  const monthlyPayment =
    monthlyRate === 0
      ? principal / totalPayments
      : (principal * monthlyRate) / (1 - Math.pow(1 + monthlyRate, -totalPayments));

  const years: MortgageYear[] = [];
  let balance = principal;
  for (let year = 1; year <= holdYears; year++) {
    const opening = balance;
    let yearPrincipal = 0;
    let yearInterest = 0;
    let yearDebt = 0;
    for (let month = 1; month <= 12; month++) {
      if (balance <= 1e-10) break;
      const interest = balance * monthlyRate;
      let principalPaid = monthlyPayment - interest;
      if (principalPaid > balance) principalPaid = balance;
      if (principalPaid < 0) die("negative principal payment encountered; check loan inputs");
      balance -= principalPaid;
      yearPrincipal += principalPaid;
      yearInterest += interest;
      yearDebt += principalPaid + interest;
    }
    years.push({
      year,
      opening_balance: opening,
      principal_paid: yearPrincipal,
      interest_paid: yearInterest,
      debt_service: yearDebt,
      ending_balance: Math.max(0, balance),
    });
  }

  return {
    principal,
    monthly_payment: monthlyPayment,
    years,
  };
}

function buildDepreciationPlan(
  purchase: PurchaseInput,
  tax: TaxInput,
  holdYears: number,
  buildingRecoveryYears: number
): DepreciationPlan {
  const totalBasis = purchase.purchase_price + purchase.capitalizable_closing_costs;
  const landBasis = totalBasis * tax.land_value_share;
  const depreciableBasis = totalBasis - landBasis;
  const costSegBasis = depreciableBasis * tax.cost_seg_share;
  const buildingBasis = depreciableBasis - costSegBasis;

  const federalBonus = costSegBasis * tax.bonus_depreciation_rate;
  const federalRemainingCostSeg = costSegBasis - federalBonus;
  const federalCostSegAnnual = federalRemainingCostSeg / tax.cost_seg_recovery_years;
  const federalBuildingAnnual = buildingBasis / buildingRecoveryYears;

  const stateBonus = tax.state_bonus_conforms ? federalBonus : 0;
  const stateRemainingCostSeg = costSegBasis - stateBonus;
  const stateCostSegAnnual = stateRemainingCostSeg / tax.cost_seg_recovery_years;
  const stateBuildingAnnual = buildingBasis / buildingRecoveryYears;

  const years: DepreciationYear[] = [];
  let fedCostSegRemaining = federalRemainingCostSeg;
  let fedBuildingRemaining = buildingBasis;
  let stateCostSegRemaining = stateRemainingCostSeg;
  let stateBuildingRemaining = buildingBasis;
  for (let year = 1; year <= holdYears; year++) {
    const yearFederalBonus = year === 1 ? federalBonus : 0;
    const yearStateBonus = year === 1 ? stateBonus : 0;
    const yearFederalCostSeg = Math.min(fedCostSegRemaining, federalCostSegAnnual);
    const yearFederalBuilding = Math.min(fedBuildingRemaining, federalBuildingAnnual);
    const yearStateCostSeg = Math.min(stateCostSegRemaining, stateCostSegAnnual);
    const yearStateBuilding = Math.min(stateBuildingRemaining, stateBuildingAnnual);
    fedCostSegRemaining = Math.max(0, fedCostSegRemaining - yearFederalCostSeg);
    fedBuildingRemaining = Math.max(0, fedBuildingRemaining - yearFederalBuilding);
    stateCostSegRemaining = Math.max(0, stateCostSegRemaining - yearStateCostSeg);
    stateBuildingRemaining = Math.max(0, stateBuildingRemaining - yearStateBuilding);

    const y: DepreciationYear = {
      year,
      federal_bonus: yearFederalBonus,
      federal_cost_seg: yearFederalCostSeg,
      federal_building: yearFederalBuilding,
      federal_total: yearFederalBonus + yearFederalCostSeg + yearFederalBuilding,
      state_bonus: yearStateBonus,
      state_cost_seg: yearStateCostSeg,
      state_building: yearStateBuilding,
      state_total: yearStateBonus + yearStateCostSeg + yearStateBuilding,
    };
    years.push(y);
  }

  const totals = years.reduce(
    (acc, y) => {
      acc.federal_bonus += y.federal_bonus;
      acc.federal_cost_seg += y.federal_cost_seg;
      acc.federal_building += y.federal_building;
      acc.federal_total += y.federal_total;
      acc.state_bonus += y.state_bonus;
      acc.state_cost_seg += y.state_cost_seg;
      acc.state_building += y.state_building;
      acc.state_total += y.state_total;
      return acc;
    },
    {
      federal_bonus: 0,
      federal_cost_seg: 0,
      federal_building: 0,
      federal_total: 0,
      state_bonus: 0,
      state_cost_seg: 0,
      state_building: 0,
      state_total: 0,
    }
  );

  return {
    building_recovery_years: buildingRecoveryYears,
    building_basis: buildingBasis,
    cost_seg_basis: costSegBasis,
    land_basis: landBasis,
    years,
    totals,
  };
}

function deriveAnnualRevenue(mode: ModeInput): number | null {
  if (mode.revenue.annual_gross_revenue !== null) return mode.revenue.annual_gross_revenue;
  if (
    mode.revenue.adr !== null &&
    mode.revenue.occupancy_rate !== null &&
    mode.revenue.available_nights !== null
  ) {
    return mode.revenue.adr * mode.revenue.occupancy_rate * mode.revenue.available_nights;
  }
  return null;
}

function strRevenueConsistency(mode: ModeInput): { impliedAnnual: number; relativeDiff: number } | null {
  if (
    mode.revenue.annual_gross_revenue === null ||
    mode.revenue.adr === null ||
    mode.revenue.occupancy_rate === null ||
    mode.revenue.available_nights === null
  ) {
    return null;
  }
  const impliedAnnual = mode.revenue.adr * mode.revenue.occupancy_rate * mode.revenue.available_nights;
  const denominator = Math.max(1, Math.abs(impliedAnnual));
  const relativeDiff = Math.abs(mode.revenue.annual_gross_revenue - impliedAnnual) / denominator;
  return { impliedAnnual, relativeDiff };
}

function projected(value: number, growthRate: number, yearIndex: number): number {
  return value * Math.pow(1 + growthRate, yearIndex);
}

function operatingBreakdown(
  modeName: ModeName,
  mode: ModeInput,
  annualRevenue: number,
  yearIndex: number,
  rentedDaysFallback: number
): OperatingBreakdown {
  const grossRevenue = projected(annualRevenue, mode.revenue_growth_rate, yearIndex);
  const otherIncome = projected(mode.other_income, mode.revenue_growth_rate, yearIndex);
  const egi = (grossRevenue + otherIncome) * (1 - mode.vacancy_rate);

  const fixedBase =
    mode.expenses.property_tax +
    mode.expenses.insurance +
    mode.expenses.hoa +
    mode.expenses.utilities +
    mode.expenses.fixed_other;
  const fixedExpenses = projected(fixedBase, mode.expense_growth_rate, yearIndex);

  const occupiedNightsRaw =
    mode.revenue.occupancy_rate !== null && mode.revenue.available_nights !== null
      ? mode.revenue.occupancy_rate * mode.revenue.available_nights
      : rentedDaysFallback;
  const occupiedNights = Math.max(0, occupiedNightsRaw);

  const variable =
    egi * mode.expenses.management_fee_rate +
    egi * mode.expenses.maintenance_rate +
    egi * mode.expenses.capex_reserve_rate +
    grossRevenue * mode.expenses.platform_fee_rate +
    grossRevenue * mode.expenses.cleaning_fee_rate +
    grossRevenue * mode.expenses.lodging_tax_rate +
    occupiedNights * mode.expenses.lodging_tax_per_night;

  const opEx = fixedExpenses + variable;
  const noi = egi - opEx;
  if (modeName === "ltr" && mode.expenses.lodging_tax_rate > 0) {
    // valid but unusual; keep as-is.
  }

  return {
    fixed_expenses: fixedExpenses,
    variable_expenses: variable,
    operating_expenses: opEx,
    effective_gross_income: egi,
    noi,
    occupied_nights: occupiedNights,
  };
}

interface TaxApplyInput {
  taxable_income: number;
  tax_rate: number;
  passive: boolean;
  section280a_limited: boolean;
  allowance_available: number;
  at_risk_remaining: number | null;
}

interface TaxApplyOutput {
  tax_due: number;
  tax_savings: number;
  deducted_loss: number;
  suspended_added: number;
  allowance_used: number;
  at_risk_used: number;
}

function applyTaxYear(input: TaxApplyInput): TaxApplyOutput {
  if (input.taxable_income >= 0) {
    return {
      tax_due: input.taxable_income * input.tax_rate,
      tax_savings: 0,
      deducted_loss: 0,
      suspended_added: 0,
      allowance_used: 0,
      at_risk_used: 0,
    };
  }

  const loss = -input.taxable_income;
  let deductible = 0;
  let allowanceUsed = 0;

  if (input.section280a_limited) {
    deductible = 0;
  } else if (!input.passive) {
    deductible = loss;
  } else {
    deductible = Math.min(loss, input.allowance_available);
    allowanceUsed = deductible;
  }

  let atRiskUsed = 0;
  if (input.at_risk_remaining !== null) {
    const capped = Math.min(deductible, input.at_risk_remaining);
    atRiskUsed = capped;
    deductible = capped;
  }

  return {
    tax_due: 0,
    tax_savings: deductible * input.tax_rate,
    deducted_loss: deductible,
    suspended_added: loss - deductible,
    allowance_used: allowanceUsed,
    at_risk_used: atRiskUsed,
  };
}

interface IrrResult {
  irr: number | null;
  error: string | null;
}

function npv(rate: number, cashflows: number[]): number {
  let total = 0;
  for (let i = 0; i < cashflows.length; i++) {
    total += cashflows[i] / Math.pow(1 + rate, i);
  }
  return total;
}

function computeIrr(cashflows: number[]): IrrResult {
  if (cashflows.length < 2) return { irr: null, error: "IRR requires at least two cashflow points." };
  const hasPositive = cashflows.some((v) => v > 0);
  const hasNegative = cashflows.some((v) => v < 0);
  if (!hasPositive || !hasNegative) {
    return { irr: null, error: "IRR undefined: cashflows must include at least one positive and one negative value." };
  }

  let low = -0.9999;
  let high = 1;
  let fLow = npv(low, cashflows);
  let fHigh = npv(high, cashflows);

  let expand = 0;
  while (fLow * fHigh > 0 && expand < 30) {
    high *= 2;
    if (high > 200) break;
    fHigh = npv(high, cashflows);
    expand++;
  }
  if (fLow * fHigh > 0) {
    return {
      irr: null,
      error: "IRR could not be solved: no NPV sign change found across search bounds.",
    };
  }

  for (let i = 0; i < 200; i++) {
    const mid = (low + high) / 2;
    const fMid = npv(mid, cashflows);
    if (Math.abs(fMid) < 1e-9) return { irr: mid, error: null };
    if (fLow * fMid <= 0) {
      high = mid;
      fHigh = fMid;
    } else {
      low = mid;
      fLow = fMid;
    }
  }
  return { irr: (low + high) / 2, error: null };
}

interface GateResult {
  blocked: boolean;
  reasons: string[];
  unavailable: string[];
  warnings: string[];
  annualRevenue: number | null;
}

function evaluateGates(modeName: ModeName, mode: ModeInput): GateResult {
  const reasons: string[] = [];
  const unavailable: string[] = [];
  const warnings: string[] = [];
  if (!mode.enabled) {
    return { blocked: false, reasons, unavailable, warnings, annualRevenue: null };
  }

  if (mode.legal.status !== "ALLOWED") {
    reasons.push(`${modeName.toUpperCase()} legal status is ${mode.legal.status}.`);
  }
  if (mode.legal.jurisdiction_evidence.length === 0) {
    reasons.push(
      `${modeName.toUpperCase()} blocked: missing address-level jurisdiction evidence for legal use rights.`
    );
  }
  if (mode.legal.hoa_evidence.length === 0) {
    reasons.push(
      `${modeName.toUpperCase()} blocked: missing HOA/title evidence (HOA allowance or no-HOA title confirmation).`
    );
  }

  if (modeName === "str") {
    if (mode.revenue.status === "UNAVAILABLE") {
      reasons.push("STR blocked: revenue data is UNAVAILABLE.");
      unavailable.push("modes.str.revenue");
    } else {
      if (mode.revenue.source_type === "airdna_pricelabs") {
        // pass
      } else if (mode.revenue.source_type === "comps" && (mode.revenue.comps_count ?? 0) >= 3) {
        // pass
      } else {
        reasons.push("STR blocked: ADR/occupancy must come from AirDNA/PriceLabs or >=3 comps.");
      }
    }
    const consistency = strRevenueConsistency(mode);
    if (consistency !== null) {
      if (consistency.relativeDiff > 0.05) {
        reasons.push(
          `STR blocked: annual_gross_revenue is materially inconsistent with ADR*occupancy*available_nights (relative diff ${round(
            consistency.relativeDiff * 100,
            2
          )}%).`
        );
      } else if (consistency.relativeDiff > 0.02) {
        warnings.push(
          `STR revenue consistency warning: annual_gross_revenue differs from ADR*occupancy*available_nights by ${round(
            consistency.relativeDiff * 100,
            2
          )}%.`
        );
      }
    }
  } else {
    if (mode.revenue.status === "UNAVAILABLE") {
      reasons.push("LTR blocked: revenue data is UNAVAILABLE.");
      unavailable.push("modes.ltr.revenue");
    } else if (mode.revenue.status === "VERIFIED") {
      const hasCompsPacket = mode.revenue.source_type === "comps" && (mode.revenue.comps_count ?? 0) >= 3;
      const hasBrokerOpinion = mode.revenue.source_type === "broker_opinion";
      if (!hasCompsPacket && !hasBrokerOpinion) {
        reasons.push(
          "LTR blocked: VERIFIED revenue requires >=3 cited comps or a broker/property-manager rent opinion; listing-site estimates cannot qualify as VERIFIED."
        );
      }
    }
  }

  const annualRevenue = deriveAnnualRevenue(mode);
  if (annualRevenue === null) {
    reasons.push(`${modeName.toUpperCase()} blocked: annual gross revenue cannot be derived.`);
    unavailable.push(`modes.${modeName}.revenue.annual_gross_revenue`);
  }

  if (mode.revenue.status === "HYPOTHETICAL") {
    warnings.push(`${modeName.toUpperCase()} revenue inputs are labeled hypothetical.`);
  }

  return {
    blocked: reasons.length > 0,
    reasons,
    unavailable,
    warnings,
    annualRevenue,
  };
}

function breakEvenStrOccupancy(
  modeName: ModeName,
  mode: ModeInput,
  debtServiceYear1: number
): number | "[UNAVAILABLE]" {
  if (modeName !== "str") return UNAVAILABLE;
  if (mode.revenue.adr === null || mode.revenue.available_nights === null) return UNAVAILABLE;
  const fixed =
    mode.expenses.property_tax +
    mode.expenses.insurance +
    mode.expenses.hoa +
    mode.expenses.utilities +
    mode.expenses.fixed_other;
  const variableRate =
    mode.expenses.management_fee_rate +
    mode.expenses.maintenance_rate +
    mode.expenses.capex_reserve_rate +
    mode.expenses.platform_fee_rate +
    mode.expenses.cleaning_fee_rate +
    mode.expenses.lodging_tax_rate;
  const denomPerNight = mode.revenue.adr * (1 - variableRate) - mode.expenses.lodging_tax_per_night;
  const denom = mode.revenue.available_nights * denomPerNight;
  if (denom <= 0) return UNAVAILABLE;
  return (fixed + debtServiceYear1) / denom;
}

function section280aLimited(tax: TaxInput): boolean {
  const limit = Math.max(14, 0.1 * tax.rented_days);
  return tax.personal_use_days > limit;
}

interface RunScenarioResult {
  annual: AnnualCashflowRow[];
  depreciation: DepreciationPlan;
  metrics: ModeMetrics;
  suspendedFedEnd: number;
  suspendedStateEnd: number;
  exit: ExitEstimate;
  decision: "BUY" | "PASS";
  warnings: string[];
}

function runScenario(
  modeName: ModeName,
  mode: ModeInput,
  input: UnderwriteInput,
  annualRevenue: number,
  buildingRecoveryYears: number,
  mortgage: MortgageSchedule
): RunScenarioResult {
  const warnings: string[] = [];
  const dep = buildDepreciationPlan(input.purchase, input.tax, input.hold_years, buildingRecoveryYears);
  const annualRows: AnnualCashflowRow[] = [];
  const sec280a = section280aLimited(input.tax);
  if (sec280a) {
    warnings.push(
      "§280A personal-use threshold triggered; current-year loss deductions are limited in this model."
    );
  }
  if (modeName === "str" && input.tax.average_guest_stay_nights <= 7) {
    warnings.push("§469 <=7-day test affects passive classification but does not determine §168 recovery life.");
  }
  if (modeName === "str" && !input.tax.state_str_nonpassive_treatment_confirmed) {
    warnings.push("State STR nonpassive treatment is unconfirmed; state STR losses are modeled as passive.");
  }

  let suspendedFed = 0;
  let suspendedState = 0;
  let cumulativeDeductedFed = 0;
  let cumulativeDeductedState = 0;

  const ltrAllowanceFed = input.tax.active_participation_ltr ? activeParticipationAllowance(input.tax.magi) : 0;
  const ltrAllowanceState = input.tax.state_active_participation_ltr ? activeParticipationAllowance(input.tax.magi) : 0;
  const strNonPassiveFed = input.tax.average_guest_stay_nights <= 7 && input.tax.material_participation_str;
  const passiveFed = modeName === "str" ? !strNonPassiveFed : true;
  const passiveState =
    modeName === "str"
      ? input.tax.state_str_nonpassive_treatment_confirmed
        ? !input.tax.state_str_nonpassive
        : true
      : true;

  for (let i = 0; i < input.hold_years; i++) {
    const mortgageYear = mortgage.years[i];
    const yearNum = i + 1;
    const op = operatingBreakdown(modeName, mode, annualRevenue, i, input.tax.rented_days);
    const grossRevenueYear = projected(annualRevenue, mode.revenue_growth_rate, i);
    const otherIncomeYear = projected(mode.other_income, mode.revenue_growth_rate, i);
    const preTaxCashflow = op.noi - mortgageYear.debt_service;

    const depYear = dep.years[i];
    const federalTaxable = op.noi - mortgageYear.interest_paid - depYear.federal_total;
    const stateTaxable = op.noi - mortgageYear.interest_paid - depYear.state_total;
    let federalTaxableAfterSuspended = federalTaxable;
    let stateTaxableAfterSuspended = stateTaxable;
    let federalSuspendedUsed = 0;
    let stateSuspendedUsed = 0;

    if (passiveFed && federalTaxableAfterSuspended > 0 && suspendedFed > 0) {
      federalSuspendedUsed = Math.min(federalTaxableAfterSuspended, suspendedFed);
      federalTaxableAfterSuspended -= federalSuspendedUsed;
      suspendedFed -= federalSuspendedUsed;
    }
    if (passiveState && stateTaxableAfterSuspended > 0 && suspendedState > 0) {
      stateSuspendedUsed = Math.min(stateTaxableAfterSuspended, suspendedState);
      stateTaxableAfterSuspended -= stateSuspendedUsed;
      suspendedState -= stateSuspendedUsed;
    }

    const allowanceFedYear = passiveFed ? (modeName === "ltr" ? ltrAllowanceFed : 0) : 0;
    const allowanceStateYear = passiveState ? (modeName === "ltr" ? ltrAllowanceState : 0) : 0;
    const atRiskRemainingFed =
      input.tax.at_risk_limit === null ? null : Math.max(0, input.tax.at_risk_limit - cumulativeDeductedFed);
    const atRiskRemainingState =
      input.tax.at_risk_limit === null ? null : Math.max(0, input.tax.at_risk_limit - cumulativeDeductedState);

    const fedTax = applyTaxYear({
      taxable_income: federalTaxableAfterSuspended,
      tax_rate: input.tax.federal_marginal_rate,
      passive: passiveFed,
      section280a_limited: sec280a && federalTaxableAfterSuspended < 0,
      allowance_available: allowanceFedYear,
      at_risk_remaining: atRiskRemainingFed,
    });
    const stateTax = applyTaxYear({
      taxable_income: stateTaxableAfterSuspended,
      tax_rate: input.tax.state_marginal_rate,
      passive: passiveState,
      section280a_limited: sec280a && stateTaxableAfterSuspended < 0,
      allowance_available: allowanceStateYear,
      at_risk_remaining: atRiskRemainingState,
    });

    cumulativeDeductedFed += fedTax.deducted_loss;
    cumulativeDeductedState += stateTax.deducted_loss;
    suspendedFed += fedTax.suspended_added;
    suspendedState += stateTax.suspended_added;

    const afterTaxCashflow =
      preTaxCashflow - fedTax.tax_due - stateTax.tax_due + fedTax.tax_savings + stateTax.tax_savings;

    annualRows.push({
      year: yearNum,
      gross_revenue: grossRevenueYear,
      other_income: otherIncomeYear,
      effective_gross_income: op.effective_gross_income,
      operating_expenses: op.operating_expenses,
      noi: op.noi,
      debt_service: mortgageYear.debt_service,
      interest_paid: mortgageYear.interest_paid,
      principal_paid: mortgageYear.principal_paid,
      pre_tax_cashflow: preTaxCashflow,
      federal_taxable_income: federalTaxable,
      federal_taxable_after_suspended: federalTaxableAfterSuspended,
      federal_suspended_used: federalSuspendedUsed,
      state_taxable_income: stateTaxable,
      state_taxable_after_suspended: stateTaxableAfterSuspended,
      state_suspended_used: stateSuspendedUsed,
      federal_tax_due: fedTax.tax_due,
      federal_tax_savings: fedTax.tax_savings,
      state_tax_due: stateTax.tax_due,
      state_tax_savings: stateTax.tax_savings,
      after_tax_cashflow: afterTaxCashflow,
      federal_suspended_end: suspendedFed,
      state_suspended_end: suspendedState,
    });
  }

  const totalBasis = input.purchase.purchase_price + input.purchase.capitalizable_closing_costs;
  const salePrice = input.purchase.purchase_price * Math.pow(1 + input.purchase.annual_appreciation_rate, input.hold_years);
  const sellingCosts = salePrice * input.purchase.selling_cost_rate;
  const amountRealizedNet = salePrice - sellingCosts;
  const loanPayoff = mortgage.years[mortgage.years.length - 1]?.ending_balance ?? 0;
  const adjustedBasisFederal = totalBasis - dep.totals.federal_total;
  const adjustedBasisState = totalBasis - dep.totals.state_total;
  const totalGainFederal = amountRealizedNet - adjustedBasisFederal;
  const totalGainState = amountRealizedNet - adjustedBasisState;
  const taxableGainFederal = Math.max(0, totalGainFederal);
  const taxableGainState = Math.max(0, totalGainState);
  const recapture1245 = Math.min(taxableGainFederal, dep.totals.federal_cost_seg + dep.totals.federal_bonus);
  const gainAfter1245 = Math.max(0, taxableGainFederal - recapture1245);
  const unrecaptured1250 = Math.min(gainAfter1245, dep.totals.federal_building);
  const remainingCapGain = Math.max(0, gainAfter1245 - unrecaptured1250);

  const fedSaleTax =
    recapture1245 * input.tax.federal_marginal_rate +
    unrecaptured1250 * input.tax.federal_unrecaptured_1250_rate +
    remainingCapGain * input.tax.federal_capital_gains_rate;
  const stateSaleTax = taxableGainState * input.tax.state_capital_gains_rate;

  const releaseFed =
    input.tax.release_suspended_losses_on_sale && passiveFed ? suspendedFed : 0;
  const releaseState =
    input.tax.release_suspended_losses_on_sale && passiveState ? suspendedState : 0;
  const releaseTaxValue =
    releaseFed * input.tax.federal_marginal_rate + releaseState * input.tax.state_marginal_rate;

  const taxDueAfterRelease = fedSaleTax + stateSaleTax - releaseTaxValue;
  const beforeTaxSaleProceeds = amountRealizedNet - loanPayoff;
  const afterTaxSaleProceeds = beforeTaxSaleProceeds - taxDueAfterRelease;

  const exit: ExitEstimate = {
    estimated_sale_price: salePrice,
    selling_costs: sellingCosts,
    loan_payoff: loanPayoff,
    amount_realized_net: amountRealizedNet,
    adjusted_basis_federal: adjustedBasisFederal,
    adjusted_basis_state: adjustedBasisState,
    total_gain_federal: totalGainFederal,
    total_gain_state: totalGainState,
    state_taxable_gain: taxableGainState,
    section_1245_recapture: recapture1245,
    unrecaptured_1250_gain: unrecaptured1250,
    remaining_capital_gain: remainingCapGain,
    federal_tax_on_sale: fedSaleTax,
    state_tax_on_sale: stateSaleTax,
    suspended_loss_release_federal: releaseFed,
    suspended_loss_release_state: releaseState,
    suspended_loss_release_tax_value: releaseTaxValue,
    tax_due_after_release: taxDueAfterRelease,
    before_tax_sale_proceeds: beforeTaxSaleProceeds,
    after_tax_sale_proceeds: afterTaxSaleProceeds,
    estimate_note:
      "Estimated five-year exit only. Recapture and gain layers are approximate; depreciation schedules use straight-line approximations and not MACRS conventions.",
  };

  const initialCashInvested = input.purchase.down_payment + input.purchase.cash_closing_costs;
  const cashflows = [-initialCashInvested];
  for (let i = 0; i < annualRows.length; i++) {
    const base = annualRows[i].after_tax_cashflow;
    if (i === annualRows.length - 1) {
      cashflows.push(base + exit.after_tax_sale_proceeds);
    } else {
      cashflows.push(base);
    }
  }

  const irr = computeIrr(cashflows);
  if (irr.error !== null) warnings.push(irr.error);

  const capRateYear1 = annualRows[0].noi / input.purchase.purchase_price;
  const dscrYear1 =
    annualRows[0].debt_service > 0 ? annualRows[0].noi / annualRows[0].debt_service : UNAVAILABLE;
  const cocYear1 =
    initialCashInvested > 0 ? annualRows[0].pre_tax_cashflow / initialCashInvested : UNAVAILABLE;
  const breakEvenOcc = breakEvenStrOccupancy(modeName, mode, annualRows[0].debt_service);

  const metrics: ModeMetrics = {
    cap_rate_year1: capRateYear1,
    dscr_year1: dscrYear1,
    cash_on_cash_year1: cocYear1,
    break_even_str_occupancy: breakEvenOcc,
    after_tax_irr: irr.irr,
    after_tax_irr_error: irr.error,
  };

  const dscrPass =
    annualRows[0].debt_service <= 0 ||
    (typeof dscrYear1 === "number" && dscrYear1 >= input.decision_hurdles.minimum_dscr);
  const cocPass =
    typeof cocYear1 === "number" && cocYear1 >= input.decision_hurdles.minimum_year1_cash_on_cash;
  const preTaxHealthy = annualRows[0].pre_tax_cashflow > 0 && dscrPass && cocPass;
  if (!preTaxHealthy) {
    warnings.push("Pre-tax economics miss hurdle; tax benefit cannot rescue a negative pre-tax deal.");
  }
  const irrPass = irr.irr !== null && irr.irr >= input.decision_hurdles.minimum_after_tax_irr;
  const decision: "BUY" | "PASS" = preTaxHealthy && irrPass ? "BUY" : "PASS";

  return {
    annual: annualRows,
    depreciation: dep,
    metrics,
    suspendedFedEnd: suspendedFed,
    suspendedStateEnd: suspendedState,
    exit,
    decision,
    warnings,
  };
}

function buildBlockedModeResult(mode: ModeInput, reasons: string[], unavailable: string[], warnings: string[]): ModeResult {
  return {
    status: "BLOCKED",
    decision: "BLOCKED",
    blocked_reasons: reasons,
    warnings,
    unavailable_fields: unavailable,
    legal_status: mode.legal.status,
    revenue_status: mode.revenue.status,
    metrics: {
      cap_rate_year1: UNAVAILABLE,
      dscr_year1: UNAVAILABLE,
      cash_on_cash_year1: UNAVAILABLE,
      break_even_str_occupancy: UNAVAILABLE,
      after_tax_irr: null,
      after_tax_irr_error: "Mode blocked before computation.",
    },
    annual_cashflows: [],
    depreciation: UNAVAILABLE,
    suspended_losses: {
      federal_end: UNAVAILABLE,
      state_end: UNAVAILABLE,
      release_assumed_on_sale: false,
    },
    exit_estimate: UNAVAILABLE,
    recovery_year_sensitivity: [],
  };
}

function analyzeMode(
  modeName: ModeName,
  mode: ModeInput,
  input: UnderwriteInput,
  mortgage: MortgageSchedule
): ModeResult {
  if (!mode.enabled) {
    return {
      status: "DISABLED",
      decision: "DISABLED",
      blocked_reasons: [],
      warnings: [],
      unavailable_fields: [],
      legal_status: mode.legal.status,
      revenue_status: mode.revenue.status,
      metrics: {
        cap_rate_year1: UNAVAILABLE,
        dscr_year1: UNAVAILABLE,
        cash_on_cash_year1: UNAVAILABLE,
        break_even_str_occupancy: UNAVAILABLE,
        after_tax_irr: null,
        after_tax_irr_error: "Mode disabled.",
      },
      annual_cashflows: [],
      depreciation: UNAVAILABLE,
      suspended_losses: {
        federal_end: UNAVAILABLE,
        state_end: UNAVAILABLE,
        release_assumed_on_sale: false,
      },
      exit_estimate: UNAVAILABLE,
      recovery_year_sensitivity: [],
    };
  }

  const gate = evaluateGates(modeName, mode);
  if (gate.blocked || gate.annualRevenue === null) {
    return buildBlockedModeResult(mode, gate.reasons, gate.unavailable, gate.warnings);
  }

  const buildingYears =
    modeName === "ltr" ? input.tax.building_recovery_years_ltr : input.tax.building_recovery_years_str;
  const baseScenario = runScenario(modeName, mode, input, gate.annualRevenue, buildingYears, mortgage);
  const sensitivity: SensitivitySummary[] = [];

  if (modeName === "str" && input.tax.building_recovery_years_str_sensitivity.length > 0) {
    const seen = new Set<number>();
    for (const years of input.tax.building_recovery_years_str_sensitivity) {
      if (seen.has(years)) continue;
      seen.add(years);
      const s = runScenario(modeName, mode, input, gate.annualRevenue, years, mortgage);
      sensitivity.push({
        building_recovery_years: years,
        year1_after_tax_cashflow: s.annual[0].after_tax_cashflow,
        year1_federal_taxable_income: s.annual[0].federal_taxable_income,
        after_tax_irr: s.metrics.after_tax_irr,
        after_tax_irr_error: s.metrics.after_tax_irr_error,
      });
    }
  }

  let decision: "BUY" | "PASS" = baseScenario.decision;
  const decisionWarnings: string[] = [];
  if (input.hypothetical) {
    decisionWarnings.push(
      `${modeName.toUpperCase()} forced to PASS because top-level hypothetical=true; BUY decisions require verified, non-hypothetical inputs.`
    );
    decision = "PASS";
  }
  if (mode.revenue.status !== "VERIFIED") {
    decisionWarnings.push(
      `${modeName.toUpperCase()} forced to PASS because revenue.status=${mode.revenue.status}; BUY decisions require VERIFIED revenue.`
    );
    decision = "PASS";
  }

  return {
    status: "ANALYZED",
    decision,
    blocked_reasons: [],
    warnings: [...gate.warnings, ...baseScenario.warnings, ...decisionWarnings],
    unavailable_fields: gate.unavailable,
    legal_status: mode.legal.status,
    revenue_status: mode.revenue.status,
    metrics: baseScenario.metrics,
    annual_cashflows: baseScenario.annual,
    depreciation: baseScenario.depreciation,
    suspended_losses: {
      federal_end: baseScenario.suspendedFedEnd,
      state_end: baseScenario.suspendedStateEnd,
      release_assumed_on_sale: input.tax.release_suspended_losses_on_sale,
    },
    exit_estimate: baseScenario.exit,
    recovery_year_sensitivity: sensitivity,
  };
}

function comparativeVerdict(ltr: ModeResult, str: ModeResult): "BUY_LTR" | "BUY_STR" | "BUY_EITHER" | "PASS" | "BLOCKED" {
  const ltrBuy = ltr.decision === "BUY";
  const strBuy = str.decision === "BUY";
  const ltrBlocked = ltr.status === "BLOCKED";
  const strBlocked = str.status === "BLOCKED";

  if (ltrBuy && strBuy) return "BUY_EITHER";
  if (ltrBuy) return "BUY_LTR";
  if (strBuy) return "BUY_STR";
  if (ltrBlocked && strBlocked) return "BLOCKED";
  return "PASS";
}

function ensureFinite(value: unknown, path = "root"): void {
  if (typeof value === "number" && !Number.isFinite(value)) {
    die(`non-finite numeric output at ${path}`);
  }
  if (Array.isArray(value)) {
    for (let i = 0; i < value.length; i++) ensureFinite(value[i], `${path}[${i}]`);
    return;
  }
  if (isRecord(value)) {
    for (const [k, v] of Object.entries(value)) ensureFinite(v, `${path}.${k}`);
  }
}

function formatOutput(input: UnderwriteInput, ltr: ModeResult, str: ModeResult): UnderwriteOutput {
  const assumptions: string[] = [
    "Educational model only; verify legal and tax treatment with counsel/CPA before decisions.",
    "No network calls were used by this calculator.",
    "Tax and legal outputs are parameterized mechanics, not legal/tax advice.",
    "Revenue evidence strings/URLs are reviewed by the analyst plus skeptic; this calculator only enforces declared status/source-type shape.",
    "Federal bonus depreciation and state conformity are explicit inputs, not hardcoded constants.",
    "Depreciation uses simplified straight-line approximations with remaining-basis caps; actual MACRS conventions require CPA-grade software.",
    "Sale recapture and gain-layer taxes are underwriting estimates, not filing-ready tax workpapers.",
  ];
  if (section280aLimited(input.tax)) {
    assumptions.push("§280A personal-use threshold is triggered by inputs; current loss use is limited.");
  }
  if (input.hypothetical) {
    assumptions.push("Input is labeled hypothetical.");
  }
  let verdict = comparativeVerdict(ltr, str);
  const hasUnverifiedModeRevenue =
    (ltr.status !== "DISABLED" && ltr.revenue_status !== "VERIFIED") ||
    (str.status !== "DISABLED" && str.revenue_status !== "VERIFIED");
  const outputWarnings = [...ltr.warnings, ...str.warnings];
  if ((input.hypothetical || hasUnverifiedModeRevenue) && verdict.startsWith("BUY")) {
    verdict = "PASS";
    outputWarnings.push(
      "Comparative verdict forced to PASS because hypothetical and/or non-VERIFIED revenue inputs are present."
    );
  }

  const output: UnderwriteOutput = {
    as_of: input.as_of,
    label: input.label,
    hypothetical: input.hypothetical,
    assumptions,
    unavailable_fields: [...ltr.unavailable_fields, ...str.unavailable_fields],
    warnings: outputWarnings,
    mode_results: {
      ltr,
      str,
    },
    comparative_verdict: verdict,
  };
  return output;
}

function main(): void {
  const inputPath = process.argv[2];
  if (!inputPath) {
    die("usage: bun .agents/skills/rental-underwriting/scripts/underwrite.ts <input.json>");
  }

  const rawText = Bun.file(inputPath).text().catch(() => {
    die(`could not read input file: ${inputPath}`);
  });

  rawText.then((text) => {
    let parsed: unknown;
    try {
      parsed = JSON.parse(text);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      die(`invalid JSON: ${msg}`);
    }

    const input = parseInput(parsed);
    const principal = input.purchase.purchase_price - input.purchase.down_payment;
    if (principal < 0) die("loan principal cannot be negative after down payment");

    const mortgage = mortgageSchedule(
      principal,
      input.purchase.loan.annual_interest_rate,
      input.purchase.loan.amortization_years,
      input.hold_years
    );

    const ltr = analyzeMode("ltr", input.modes.ltr, input, mortgage);
    const str = analyzeMode("str", input.modes.str, input, mortgage);

    const output = formatOutput(input, ltr, str);
    ensureFinite(output);

    const printable = JSON.stringify(
      output,
      (_key, value) => (typeof value === "number" ? round(value, 6) : value),
      2
    );
    console.log(printable);
  });
}

main();
