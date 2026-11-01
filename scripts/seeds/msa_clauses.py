"""Clause library for the synthetic Master Supply Agreements.

``build_clauses(ctx, industry)`` returns an ordered list of clauses. Each clause is
``{"title": str, "paras": [para, ...]}`` where a para is either a plain string or a dict
``{"text": str, "items": [str, ...], "key": str}``. ``key`` marks the sub-clauses whose
location is recorded in ground_truth.json (price_lock, surcharge, payment_terms, penalty).

All strings are ``str.format``-ed with ``ctx``. Numbering is applied by the package layout.
"""

from __future__ import annotations


def _p(text, items=None, key=None):
    d = {"text": text}
    if items:
        d["items"] = items
    if key:
        d["key"] = key
    return d


def core_clauses_part1() -> list[dict]:
    return [
        {
            "title": "Definitions and Interpretation",
            "paras": [
                _p(
                    "In this Agreement the following capitalised terms shall have the meanings set out below, "
                    "unless the context clearly requires otherwise:",
                    [
                        "<b>“Agreement”</b> means this Master Supply Agreement including its Annexes, as amended from time to time in accordance with its terms;",
                        "<b>“Annex”</b> means an annex attached to this Agreement, each of which forms an integral part of it;",
                        "<b>“Business Day”</b> means any day other than a Saturday, Sunday or a public holiday in the federal state in which the Delivery Address is located;",
                        "<b>“Delivery Address”</b> means the Buyer’s central warehouse specified in Annex 2 or any other receiving point notified by the Buyer in writing;",
                        "<b>“Goods”</b> means the {goods} listed in the Price List and any further items that the Parties may add to the Price List by written amendment;",
                        "<b>“Order”</b> means a purchase order issued by the Buyer under this Agreement in accordance with {c_ordering};",
                        "<b>“Order Confirmation”</b> means the Supplier’s written acceptance of an Order;",
                        "<b>“Price List”</b> means the list of Goods and unit prices set out in Annex 1;",
                        "<b>“Purchasing Department”</b> means the {approval_dept} of the Buyer, acting through its authorised signatories;",
                        "<b>“Specification”</b> means the technical description of the Goods, including any drawings, data sheets and standards referred to in the Order or in the Price List;",
                        "<b>“Written”</b> or <b>“in writing”</b> includes signed letters and, unless stated otherwise, e-mail exchanged between the contact persons named in Annex 2, but excludes text messages and messenger services.",
                    ],
                ),
                "Headings are inserted for convenience only and do not affect the interpretation of this Agreement. "
                "Words in the singular include the plural and vice versa. The words “including” and “in particular” "
                "are illustrative and do not limit the generality of the preceding words.",
                "References to statutory provisions are references to those provisions as amended or re-enacted from "
                "time to time. Where a German legal term is the accurate equivalent of an English expression used in "
                "this Agreement, the German term shall prevail for the purpose of interpretation.",
            ],
        },
        {
            "title": "Subject Matter and Scope",
            "paras": [
                "This Agreement sets out the framework conditions under which the Supplier shall sell and deliver "
                "Goods to the Buyer. It does not by itself oblige the Buyer to purchase any particular quantity of "
                "Goods; purchase obligations arise only from individual Orders accepted in accordance with this Agreement.",
                "The Agreement applies to all Orders placed by the Buyer with the Supplier for Goods during its term, "
                "irrespective of whether the Order expressly refers to this Agreement. Orders placed by affiliated "
                "companies of the Buyer are covered only if the affiliate has acceded to this Agreement in writing.",
                "General terms and conditions of the Supplier, in particular terms printed on order confirmations, "
                "delivery notes, invoices or published on the Supplier’s website, shall not apply, even if the Buyer "
                "does not expressly object to them or accepts deliveries without reservation.",
                "The Supplier acknowledges that the Buyer relies on the continuity of supply of the Goods for its own "
                "production and shipping operations, and that the Supplier has been selected in part because of its "
                "ability to deliver reliably from stock within the lead times agreed in this Agreement.",
            ],
        },
        {
            "title": "Contract Documents and Order of Precedence",
            "paras": [
                _p(
                    "In the event of any conflict or inconsistency between the documents forming the contractual "
                    "relationship, the following order of precedence shall apply:",
                    [
                        "the individual Order, but only to the extent it expressly deviates from this Agreement and has been signed by the Purchasing Department;",
                        "the main body of this Agreement;",
                        "Annex 1 (Price List);",
                        "Annex 2 (Delivery Address and Contact Persons);",
                        "the Specification;",
                        "the statutory provisions.",
                    ],
                ),
                "Amendments to this Agreement, including amendments to Annex 1, are valid only if made in writing "
                "and signed by authorised representatives of both Parties. This requirement may itself be waived only "
                "in writing. Individual agreements made orally remain unaffected but must be confirmed in writing to be evidenced.",
            ],
        },
        {
            "title": "Forecasts and Capacity Planning",
            "paras": [
                "The Buyer may provide the Supplier with rolling forecasts of its expected requirements for the "
                "following {forecast_months} months. Forecasts are provided for planning purposes only and do not "
                "constitute Orders or any commitment to purchase.",
                "The Supplier shall use forecasts to plan its own procurement and stock levels and shall inform the "
                "Buyer without delay if it anticipates that it will not be able to meet the forecast volumes or the "
                "lead times set out in {c_delivery_dates}.",
                "Where the Buyer has expressly authorised in writing the procurement of specific raw materials or "
                "components beyond the regular lead time, the Buyer shall compensate the Supplier for unavoidable, "
                "documented costs of such authorised materials if no corresponding Orders are placed within six months "
                "of the authorisation. Any further compensation for forecast deviations is excluded.",
            ],
        },
        {
            "title": "Ordering Process",
            "paras": [
                "Orders shall be issued by the Buyer in writing using the Buyer’s purchase order form and shall "
                "state at least the order number, the reference to this Agreement, the item numbers from the Price "
                "List, the quantities, the unit prices, the requested delivery date and the Delivery Address.",
                "Only Orders issued by the Purchasing Department are binding on the Buyer. Requests or call-offs made "
                "by other departments, including warehouse or production staff, do not constitute Orders unless "
                "subsequently confirmed by a purchase order of the Purchasing Department.",
                "The Supplier shall confirm each Order in writing within {confirm_days} Business Days of receipt, "
                "quoting the Buyer’s order number. If the Supplier does not reject an Order within that period, the "
                "Order shall be deemed accepted on the terms stated in it.",
                "An Order Confirmation that deviates from the Order in respect of item, quantity, price or delivery "
                "date constitutes a new offer and binds the Buyer only if accepted by the Purchasing Department in writing.",
                "The Supplier shall quote the Buyer’s order number on all correspondence, delivery notes and invoices "
                "relating to an Order. Documents that do not bear the order number may be returned unprocessed.",
            ],
        },
        {
            "title": "Order Changes and Cancellation",
            "paras": [
                "The Buyer may request changes to quantities or delivery dates of an accepted Order. The Supplier "
                "shall accommodate such requests to the extent reasonable and shall inform the Buyer within two "
                "Business Days of any effect on delivery dates.",
                "The Buyer may cancel an accepted Order, in whole or in part, free of charge up to {cancel_days} "
                "Business Days before the confirmed delivery date, provided that the Goods concerned are standard "
                "catalogue items that the Supplier keeps in stock for other customers.",
                "Changes or cancellations requested by the Supplier require the prior written consent of the Buyer.",
            ],
        },
        {
            "title": "Electronic Ordering and Communication",
            "paras": [
                "The Parties intend to exchange Orders, Order Confirmations, dispatch advices and invoices "
                "electronically. Until an electronic data interchange connection has been tested and released by "
                "both Parties, documents shall be exchanged as PDF attachments by e-mail between the addresses in Annex 2.",
                "Each Party shall take appropriate technical and organisational measures to protect its systems "
                "against unauthorised access, malware and manipulation of electronically transmitted documents, and "
                "shall inform the other Party without delay of any security incident that may affect such documents.",
                "Documents transmitted electronically are deemed received when they become available in the "
                "recipient’s mailbox or system on a Business Day before 4 p.m.; otherwise on the next Business Day.",
            ],
        },
        {
            "title": "Prices and Price List",
            "paras": [
                "The prices for the Goods are set out in the Price List in Annex 1. The prices are stated in euro "
                "(EUR) and are net prices exclusive of statutory value added tax, which shall be shown separately in "
                "the invoice at the rate applicable on the date of supply.",
                "Unless expressly stated otherwise in Annex 1, the prices include packaging suitable for the mode of "
                "transport, loading, freight, transport insurance and delivery to the Delivery Address in accordance "
                "with the agreed Incoterm, as well as all certificates and documentation required under this Agreement.",
                _p(
                    "The prices set out in the Price List are fixed for a period of {lock_months} months from the "
                    "Effective Date of this Agreement, i.e. until and including {lock_end} (the “Price Lock Period”). "
                    "During the Price Lock Period the Supplier shall not increase any price, irrespective of changes in "
                    "the cost of raw materials, energy, wages, transport or exchange rates. Orders placed during the "
                    "Price Lock Period shall be invoiced at the Price List prices even if delivery takes place after "
                    "the end of the Price Lock Period.",
                    key="price_lock",
                ),
                "After expiry of the Price Lock Period, either Party may request a review of the Price List. Any "
                "price adjustment requires a written amendment to Annex 1 signed by both Parties and shall apply only "
                "to Orders placed after the amendment has been signed. Until such amendment, the existing prices continue to apply.",
                "If the Supplier offers comparable goods to other customers of similar volume at lower prices or on "
                "more favourable terms, it shall inform the Buyer and offer the same conditions to the Buyer.",
            ],
        },
        {
            "title": "Quality and Specifications",
            "paras": [
                "The Supplier shall deliver Goods that conform to the Specification, to the applicable DIN, EN and ISO "
                "standards stated in the Price List and to the generally recognised rules of technology. The Supplier "
                "shall maintain a quality management system certified to ISO 9001 or an equivalent standard throughout "
                "the term of this Agreement and shall provide the Buyer with a copy of the current certificate on request.",
                "The Supplier shall not change materials, manufacturing processes, sub-suppliers or production sites "
                "for the Goods without giving the Buyer at least three months’ prior written notice. The Buyer may "
                "require samples and test reports before such a change takes effect.",
                "The Supplier shall keep records allowing the traceability of each delivery back to the production "
                "batch for at least ten years and shall make them available to the Buyer upon request.",
            ],
        },
    ]


def industry_packaging() -> list[dict]:
    return [
        {
            "title": "Technical Requirements for Packaging Materials",
            "paras": [
                "Corrugated board packaging shall comply with the board grade, flute and burst strength stated in the "
                "Price List. The moisture content of cartons on delivery shall not exceed 10 %. Cartons shall be "
                "delivered flat-packed, strapped and on pallets protected against moisture.",
                "Films and adhesive tapes shall be stored and transported by the Supplier at temperatures between "
                "+5 °C and +30 °C. Rolls shall be wound evenly on cores of the stated diameter and shall be free of "
                "telescoping, creases and contamination.",
                "Packaging materials shall be free of substances of very high concern above the thresholds stipulated "
                "by the REACH Regulation and shall comply with the German Packaging Act to the extent applicable to the Buyer.",
            ],
        },
        {
            "title": "Fastener Conformity and Traceability",
            "paras": [
                "Fasteners shall conform to the dimensional standards and property classes stated in the Price List. "
                "Each packaging unit shall be labelled with the standard designation, dimension, property class, "
                "surface treatment, manufacturer’s mark and batch number.",
                "On request, the Supplier shall provide an inspection certificate 3.1 in accordance with EN 10204 for "
                "each batch of fasteners of property class 8.8 or higher. Certificates shall be available "
                "electronically no later than the delivery date.",
                "Zinc-plated fasteners shall be free of hexavalent chromium. Fasteners of property class 10.9 or "
                "higher shall be delivered only after a suitable hydrogen embrittlement relief treatment.",
            ],
        },
    ]


def industry_electronics() -> list[dict]:
    return [
        {
            "title": "ESD Protection and Moisture Sensitivity",
            "paras": [
                "The Supplier shall handle, store and pack all electrostatic-sensitive components in accordance with "
                "IEC 61340-5-1. Components shall be delivered in ESD-protective packaging marked with the appropriate warning symbol.",
                "Moisture-sensitive devices shall be delivered in sealed moisture barrier bags with desiccant and "
                "humidity indicator card, labelled with the moisture sensitivity level and the bag seal date in "
                "accordance with J-STD-033. The remaining floor life on delivery shall be at least 80 %.",
                "Reels and trays shall carry labels stating the manufacturer part number, the Supplier item number, "
                "quantity, date code and lot number, both in plain text and as a machine-readable 2D code.",
            ],
        },
        {
            "title": "Authenticity of Components and Counterfeit Prevention",
            "paras": [
                "The Supplier warrants that all Goods are new, unused and genuine and have been procured directly from "
                "the original component manufacturer or from that manufacturer’s authorised distribution channel.",
                "The Supplier shall operate a counterfeit-prevention process consistent with recognised industry "
                "practice and shall provide a certificate of conformance and, on request, the manufacturer’s "
                "traceability documentation for every delivery.",
                "If counterfeit or suspect components are discovered, the Supplier shall replace them immediately with "
                "genuine components and shall bear all costs of investigation, removal and rework, without prejudice "
                "to any further claims of the Buyer.",
            ],
        },
        {
            "title": "Product Change Notifications and Obsolescence",
            "paras": [
                "The Supplier shall forward to the Buyer every product change notification and every end-of-life "
                "notification received from a component manufacturer for any Goods within five Business Days of receipt.",
                "Where a component is discontinued, the Supplier shall offer the Buyer a last-time-buy opportunity of "
                "at least six months and shall support the Buyer in identifying and qualifying a form-, fit- and "
                "function-compatible alternative.",
                "Compliance with the RoHS Directive and the REACH Regulation shall be confirmed for every item on the "
                "Price List; any change in compliance status shall be notified without delay.",
            ],
        },
    ]


def core_clauses_part2() -> list[dict]:
    return [
        {
            "title": "Packaging, Marking and Labelling",
            "paras": [
                "The Supplier shall pack the Goods so as to prevent damage during transport and storage. Pallets shall "
                "not exceed a loaded height of 1.80 m and a gross weight of 1,000 kg unless agreed otherwise.",
                "Every delivery shall be accompanied by a delivery note stating the Buyer’s order number, the "
                "Supplier’s delivery note number, the date of dispatch, item numbers, descriptions, delivered "
                "quantities and units, and the number of packages. Partial deliveries shall be marked as such.",
                "The Supplier shall take back transport packaging free of charge at the Delivery Address or shall "
                "bear the cost of its proper disposal.",
            ],
        },
        {
            "title": "Delivery Terms and Transfer of Risk",
            "paras": [
                "Unless otherwise agreed in the Order, deliveries shall be made {incoterm} {delivery_place} "
                "(Incoterms® 2020). Risk passes to the Buyer upon unloading of the Goods at the Delivery Address.",
                "Deliveries shall be made on Business Days between {receiving_hours}. Deliveries outside these hours "
                "require prior arrangement with the Buyer’s warehouse; the Buyer may refuse acceptance of deliveries "
                "made without such arrangement.",
                "Partial deliveries and deliveries in excess of the ordered quantity are permitted only with the "
                "Buyer’s prior consent. Excess quantities may be returned at the Supplier’s cost and risk.",
                "Signature of a delivery note by the Buyer’s receiving staff confirms only the number of packages "
                "received and does not constitute acceptance of the Goods or a waiver of any rights.",
            ],
        },
        {
            "title": "Delivery Dates, Delays and Late-Delivery Penalty",
            "paras": [
                "The standard lead time for Goods listed in the Price List is {lead_time} Business Days from the date "
                "of the Order. The delivery date stated in the Order Confirmation is binding. Compliance with the "
                "delivery date is determined by the receipt of the Goods at the Delivery Address.",
                "If the Supplier becomes aware that a delivery date cannot be met, it shall notify the Buyer in "
                "writing without delay, stating the reasons and the expected duration of the delay. Such notice does "
                "not release the Supplier from its obligations.",
                _p(
                    "If the Supplier fails to meet a binding delivery date for reasons for which it is responsible, "
                    "the Buyer shall be entitled to claim a contractual penalty of {penalty_rate} of the net order "
                    "value of the delayed Goods for {penalty_unit} of delay, limited to a maximum of {penalty_cap} of "
                    "the net order value of the delayed Goods. The penalty shall be credited against any damages "
                    "claimed for the delay. The Buyer may reserve the penalty up to the time of final payment for the "
                    "delayed delivery, notwithstanding Section 341 (3) of the German Civil Code (BGB).",
                    key="penalty",
                ),
                "Further statutory rights of the Buyer, in particular the right to withdraw from the Order after "
                "expiry of a reasonable grace period and to claim damages in lieu of performance, remain unaffected.",
            ],
        },
        {
            "title": "Incoming Inspection and Notification of Defects",
            "paras": [
                "The Buyer shall inspect the Goods upon receipt only for externally visible transport damage and for "
                "identity and quantity by reference to the delivery note. Defects detected in this inspection shall "
                "be notified within ten Business Days of receipt.",
                "Defects that are not detectable in this incoming inspection shall be notified within ten Business "
                "Days of their discovery. To this extent the Supplier waives the objection of late notification "
                "under Section 377 of the German Commercial Code (HGB).",
                "The Buyer’s goods receipt record, signed by the receiving clerk, shall be prima facie evidence of the "
                "quantities actually received at the Delivery Address.",
            ],
        },
        {
            "title": "Warranty and Claims for Defects",
            "paras": [
                "The Supplier warrants that the Goods are free from defects in material and workmanship, conform to the "
                "Specification and are fit for the purpose known to the Supplier.",
                "The limitation period for claims for defects is {warranty_months} months from the passing of risk, "
                "unless a longer statutory period applies. For replaced or repaired Goods the limitation period begins anew.",
                "In urgent cases, in particular to avert acute danger or to prevent a production stoppage, the Buyer "
                "may remedy the defect itself or have it remedied by a third party at the Supplier’s expense after "
                "informing the Supplier.",
            ],
        },
        {
            "title": "Supplier Evaluation and Continuous Improvement",
            "paras": [
                "The Buyer evaluates the Supplier at least once per calendar year on the basis of on-time delivery, "
                "delivery quantity accuracy, quality of the Goods, accuracy of delivery and invoice documents, and "
                "responsiveness. The target values are an on-time delivery rate of at least 97 % and a complaint rate "
                "of less than 0.5 % of delivered packaging units.",
                "If the Supplier fails to reach a target value in two consecutive quarters, the Parties shall agree "
                "on a corrective action plan with defined measures, responsibilities and deadlines. The Supplier shall "
                "report on its implementation monthly until the target value has been reached again.",
                "The Supplier shall submit proposals for cost reductions, simplifications of packaging and "
                "improvements in logistics at least once a year. Savings achieved through proposals of the Supplier "
                "shall be shared between the Parties as agreed on a case-by-case basis.",
            ],
        },
        {
            "title": "Invoicing Requirements",
            "paras": [
                "The Supplier shall issue a separate invoice for each delivery, no earlier than the date of delivery. "
                "Collective invoices are permitted only with the prior consent of the Buyer.",
                _p(
                    "Each invoice must comply with Section 14 of the German VAT Act (UStG) and shall in addition state:",
                    [
                        "the Buyer’s order number and the number of this Agreement;",
                        "the number of the delivery note to which it relates;",
                        "for each line the item number from the Price List, the description, the quantity, the unit, the unit price and the line total;",
                        "the net total, the applicable VAT rate, the VAT amount and the gross total;",
                        "the payment terms and the early-payment discount in accordance with this Agreement.",
                    ],
                ),
                "Invoices shall be submitted electronically in PDF or a structured e-invoice format to {invoice_email}. "
                "Invoices that do not meet these requirements may be returned by the Buyer; in that case the payment "
                "period does not begin until a compliant invoice has been received.",
                "Unit prices in an invoice shall correspond exactly to the prices in the Price List as applicable on "
                "the date of the Order. Invoiced quantities shall not exceed the quantities confirmed in the Buyer’s "
                "goods receipt.",
            ],
        },
        {
            "title": "Payment Terms and Early-Payment Discount",
            "paras": [
                _p(
                    "Payment shall be made within {net_days} days net from receipt of a proper invoice, but not before "
                    "receipt of the Goods. If the Buyer pays within {disc_days} days of receipt of a proper invoice, "
                    "it shall be entitled to deduct an early-payment discount of {disc_pct} % of the gross invoice amount.",
                    key="payment_terms",
                ),
                "For the calculation of the payment and discount periods, the later of the date of receipt of the "
                "invoice and the date of receipt of the Goods shall be decisive. Payment is deemed to have been made "
                "on time if the transfer order is placed with the Buyer’s bank before the end of the relevant period.",
                "Payments are made by bank transfer to the account stated in the invoice, which must correspond to the "
                "account stated in Annex 2. A change of bank account must be confirmed by the Supplier in a letter "
                "signed by its managing directors; e-mail notifications of changed bank details shall not be acted upon.",
                "Payment does not constitute an acknowledgement that the Goods are free from defects or that the "
                "invoice is correct.",
            ],
        },
        {
            "title": "Set-off and Retention",
            "paras": [
                "The Buyer is entitled to rights of set-off and retention to the extent permitted by law. The Supplier "
                "may set off only claims that are undisputed or have been finally determined by a court.",
                "The Supplier may not assign claims against the Buyer to third parties without the Buyer’s prior "
                "written consent; Section 354a HGB remains unaffected.",
            ],
        },
        {
            "title": "Retention of Title",
            "paras": [
                "Ownership of the Goods passes to the Buyer upon delivery, irrespective of payment of the purchase "
                "price. Any extended or prolonged retention of title of the Supplier is excluded.",
                "Where the Buyer has accepted a simple retention of title in an individual case, it shall expire at "
                "the latest upon payment for the Goods concerned. The Buyer remains entitled to process and resell "
                "the Goods in the ordinary course of business.",
            ],
        },
        {
            "title": "Personnel and Conduct at the Buyer’s Premises",
            "paras": [
                "Employees and drivers of the Supplier or its carriers shall comply with the site regulations, safety "
                "instructions and traffic rules at the Delivery Address, which are available at the gatehouse and on request.",
                "The Supplier shall ensure that drivers carry suitable personal protective equipment, in particular "
                "safety shoes and high-visibility vests, and that they remain in the areas designated for unloading.",
                "The Buyer may refuse access to persons who repeatedly or seriously breach these rules.",
            ],
        },
        {
            "title": "Compliance, Sustainability and Supply-Chain Due Diligence",
            "paras": [
                "The Supplier shall comply with all applicable laws, in particular those on minimum wages, working "
                "time, occupational safety, environmental protection, export control and anti-corruption.",
                "The Supplier acknowledges the Buyer’s Supplier Code of Conduct and shall implement appropriate "
                "measures in its own supply chain to identify and mitigate human-rights and environmental risks within "
                "the meaning of the German Supply Chain Due Diligence Act, to the extent applicable.",
                "Neither Party shall offer, promise or grant any undue advantage to employees of the other Party. "
                "Gifts and invitations exceeding a value of EUR 50 per person and year are not permitted.",
            ],
        },
        {
            "title": "Export Control and Origin of Goods",
            "paras": [
                "The Supplier shall inform the Buyer in writing, at the latest with the Order Confirmation, of any "
                "authorisation requirements under German, European or US export control law applicable to the Goods "
                "and shall state the export control classification number, if any, in its delivery documents.",
                "Upon request the Supplier shall provide long-term supplier declarations on the preferential origin "
                "of the Goods in accordance with the applicable EU implementing regulation, renewed annually without "
                "further request, and shall state the customs tariff number of each item.",
                "The Supplier shall indemnify the Buyer against all disadvantages arising from incorrect or late "
                "information on export control requirements or the origin of the Goods.",
            ],
        },
        {
            "title": "Business Continuity and Supply Assurance",
            "paras": [
                "The Supplier shall maintain a safety stock of the Goods sufficient to cover at least {safety_weeks} "
                "weeks of the Buyer’s average demand, calculated on the basis of the Orders of the preceding six months.",
                "The Supplier shall maintain a documented business continuity plan covering at least the loss of a "
                "production or warehouse site, the failure of key sub-suppliers and the failure of IT systems, and "
                "shall review it annually.",
            ],
        },
        {
            "title": "Force Majeure",
            "paras": [
                "Neither Party shall be liable for a failure to perform its obligations to the extent that the failure "
                "results from events beyond its reasonable control which could not have been foreseen or avoided with "
                "reasonable care, such as natural disasters, war, terrorism, epidemics or official orders (“Force Majeure”).",
                "Shortages of raw materials, energy or transport capacity, price increases of sub-suppliers and labour "
                "disputes within the Supplier’s own business do not constitute Force Majeure.",
                "The affected Party shall notify the other Party without delay and use reasonable efforts to mitigate "
                "the effects. If a Force Majeure event lasts longer than eight weeks, either Party may terminate the "
                "affected Orders with immediate effect.",
            ],
        },
        {
            "title": "Cost Developments, Surcharges and Additional Charges",
            "paras": [
                "The Parties acknowledge that the costs of raw materials, energy, transport and labour may fluctuate "
                "during the term of this Agreement. The Supplier has taken such fluctuations into account in the "
                "calculation of the prices in the Price List.",
                _p(
                    "Surcharges of any kind, including but not limited to fuel surcharges, energy surcharges, raw-material "
                    "or alloy surcharges, toll or freight surcharges, small-quantity surcharges, handling or "
                    "administration fees and packaging surcharges, are not permitted and shall not be invoiced unless "
                    "they have been approved in advance and in writing by the Buyer’s Purchasing Department for the "
                    "specific Order concerned. Approvals by other departments or individual employees of the Buyer are not sufficient.",
                    key="surcharge",
                ),
                "Any surcharge or additional charge shown on an invoice without such prior written approval shall "
                "not be payable. The Buyer may reject the invoice in its entirety or pay only the amount corresponding "
                "to the Price List prices; in either case no default in payment shall arise.",
                "If the Supplier considers that an extraordinary and unforeseeable change in its cost base makes "
                "performance unreasonable after the end of the Price Lock Period, it may request negotiations under "
                "the price review procedure in {c_prices}. The Supplier shall not suspend deliveries pending such negotiations.",
            ],
        },
        {
            "title": "Product Liability and Insurance",
            "paras": [
                "If a claim is made against the Buyer on the basis of product liability, the Supplier shall indemnify "
                "the Buyer against such claim to the extent the damage was caused by a defect of the Goods supplied by the Supplier.",
                "The Supplier shall maintain product and public liability insurance with a coverage of at least "
                "{insurance} per claim for the term of this Agreement and shall provide evidence of such insurance on request.",
            ],
        },
        {
            "title": "Liability",
            "paras": [
                "The Parties are liable without limitation for damages resulting from injury to life, body or health, "
                "for intentional or grossly negligent breach of duty, under the German Product Liability Act and to "
                "the extent of any guarantee given.",
                "In the event of a slightly negligent breach of an essential contractual obligation, liability is "
                "limited to the foreseeable damage typical for this type of contract. In all other cases of slight "
                "negligence the aggregate liability of each Party per contract year is limited to {liability_cap}.",
                "The above limitations do not apply to the Supplier’s obligations under the clauses on product "
                "liability, confidentiality and compliance.",
            ],
        },
        {
            "title": "Intellectual Property",
            "paras": [
                "Drawings, specifications, samples and tools provided by the Buyer remain its property and may be used "
                "by the Supplier only for performing Orders. They shall be returned on request or at the end of this Agreement.",
                "The Supplier warrants that the Goods and their use as intended do not infringe any third-party "
                "intellectual property rights in the European Union and shall indemnify the Buyer against such claims.",
            ],
        },
        {
            "title": "Confidentiality",
            "paras": [
                "Each Party shall treat as confidential all commercial and technical information of the other Party "
                "which it obtains in connection with this Agreement, including prices, volumes and the terms of this "
                "Agreement, and shall use such information only for the purposes of this Agreement.",
                "This obligation does not apply to information that was publicly available, was already lawfully known "
                "to the receiving Party, has been independently developed or must be disclosed by law or official order.",
                "The confidentiality obligation continues for {conf_years} years after termination of this Agreement. "
                "The Supplier may name the Buyer as a reference customer only with the Buyer’s prior written consent.",
            ],
        },
        {
            "title": "Data Protection",
            "paras": [
                "The Parties shall process personal data of the other Party’s contact persons only for the purpose of "
                "performing this Agreement and in compliance with the General Data Protection Regulation and the "
                "German Federal Data Protection Act.",
                "Each Party shall inform its own employees whose data are passed to the other Party about such "
                "processing in accordance with Articles 13 and 14 GDPR.",
            ],
        },
        {
            "title": "Audits",
            "paras": [
                "The Buyer or a third party bound to professional secrecy may audit the Supplier’s compliance with "
                "this Agreement, in particular with the quality and traceability requirements, after giving ten "
                "Business Days’ notice during normal business hours.",
                "Each Party bears its own costs of an audit, unless the audit reveals a material breach by the "
                "Supplier, in which case the Supplier shall reimburse the reasonable costs of the audit.",
            ],
        },
        {
            "title": "Term and Termination",
            "paras": [
                "This Agreement enters into force on {effective_date} (the “Effective Date”) and runs for an initial "
                "term of {term_years}. It is thereafter renewed automatically for successive periods of one year "
                "unless terminated by either Party with {notice} notice to the end of the relevant term.",
                _p(
                    "The right of either Party to terminate for good cause remains unaffected. Good cause for the Buyer "
                    "exists in particular if:",
                    [
                        "the Supplier repeatedly fails to meet confirmed delivery dates despite a written warning;",
                        "the Supplier invoices surcharges or prices deviating from the Price List on more than one occasion within twelve months;",
                        "insolvency proceedings are applied for or opened over the assets of the Supplier;",
                        "a change of control occurs in the Supplier and the new controlling shareholder is a competitor of the Buyer.",
                    ],
                ),
                "Termination must be made in writing to be effective.",
            ],
        },
        {
            "title": "Consequences of Termination",
            "paras": [
                "Orders accepted before the effective date of termination shall be completed under the terms of this "
                "Agreement, unless the Buyer requests otherwise.",
                "Upon termination the Supplier shall support the transition of supply to a new supplier for a period "
                "of up to three months at the prices of the Price List.",
            ],
        },
        {
            "title": "Assignment and Subcontracting",
            "paras": [
                "Neither Party may assign or transfer this Agreement or individual rights and obligations under it "
                "without the prior written consent of the other Party; consent shall not be unreasonably withheld for "
                "transfers to affiliated companies.",
                "The Supplier may subcontract the manufacture of Goods only with the Buyer’s prior written consent and "
                "remains responsible for its subcontractors as for its own acts.",
            ],
        },
        {
            "title": "Notices",
            "paras": [
                "Notices under this Agreement shall be given in writing to the addresses and contact persons stated in "
                "Annex 2. Notices of termination and of changes in bank details must in addition be sent by registered letter.",
                "Each Party shall notify the other without delay of any change in its address or contact persons.",
            ],
        },
        {
            "title": "Governing Law and Jurisdiction",
            "paras": [
                "This Agreement and all Orders shall be governed by the laws of the Federal Republic of Germany, "
                "excluding the United Nations Convention on Contracts for the International Sale of Goods (CISG) and "
                "the conflict-of-law rules.",
                "The exclusive place of jurisdiction for all disputes arising from or in connection with this "
                "Agreement is {court}. The Buyer is, however, also entitled to bring an action at the Supplier’s "
                "general place of jurisdiction.",
                "The place of performance for deliveries is the Delivery Address; the place of performance for payment "
                "is the Buyer’s registered office.",
            ],
        },
        {
            "title": "Miscellaneous",
            "paras": [
                "Should any provision of this Agreement be or become invalid or unenforceable, the validity of the "
                "remaining provisions shall not be affected. The Parties shall replace the invalid provision with a "
                "valid provision that comes as close as possible to the economic purpose of the invalid one.",
                "This Agreement is executed in two counterparts in English, of which each Party receives one. "
                "Electronic signatures complying with the eIDAS Regulation are sufficient.",
                "This Agreement constitutes the entire agreement between the Parties regarding its subject matter and "
                "supersedes all prior negotiations and arrangements.",
            ],
        },
    ]


def build_clauses(industry: str) -> list[dict]:
    extra = {"packaging": industry_packaging, "electronics": industry_electronics}[industry]()
    return core_clauses_part1() + extra + core_clauses_part2()


def clause_index(clauses: list[dict], title_prefix: str) -> int:
    """1-based number of the clause whose title starts with ``title_prefix``."""
    for i, c in enumerate(clauses, start=1):
        if c["title"].startswith(title_prefix):
            return i
    raise KeyError(title_prefix)


def annex_kpis() -> list[tuple[str, str, str, str]]:
    """Rows for the supplier-evaluation annex: KPI, definition, target, measurement."""
    return [
        ("On-time delivery", "Deliveries received at the Delivery Address on the confirmed date ÷ all deliveries", "≥ 97 %", "Quarterly, from goods receipt postings"),
        ("Quantity accuracy", "Order lines delivered in the ordered quantity ÷ all order lines", "≥ 99 %", "Quarterly, from goods receipt postings"),
        ("Complaint rate", "Packaging units with justified complaints ÷ packaging units delivered", "< 0.5 %", "Quarterly, from complaint records"),
        ("Document accuracy", "Invoices passing the three-way match without clarification ÷ all invoices", "≥ 98 %", "Quarterly, from accounts payable"),
        ("Response time", "Order Confirmations received within the agreed period ÷ all Orders", "≥ 95 %", "Quarterly, from purchasing records"),
        ("Certificates", "Validity of ISO 9001 certificate and other required certificates", "valid at all times", "Annually"),
    ]


def escalation(b: dict, s: dict) -> list[tuple[str, str, str, str]]:
    """Escalation levels: level, Buyer side, Supplier side, response time."""
    return [
        ("Level 1 – operational", f"{b['contact']['name']} ({b['contact']['role']})", f"{s['contact']['name']} ({s['contact']['role']})", "1 Business Day"),
        ("Level 2 – management", "Head of Purchasing", "Head of Sales", "3 Business Days"),
        ("Level 3 – executive", b["managing_directors"][0] + ", Managing Director", s["managing_directors"][0] + ", Managing Director", "5 Business Days"),
    ]
