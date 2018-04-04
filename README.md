# salsa-verde
Trying to make a system out of SALSA's forms

# Spec

## Worksheets

### COM 01 Complaint Summary

#### Description

For logging a complaint

#### Fields

* Date
* Author
* Reason - Bacteria, Packaging, Foreign Body, Other
* Total Stock effected

### COM 02 Complaint Log

#### Description

For investigating a complaint

#### Fields

* Date
* Author
* Type - Food safety, Specification
* Complainant Name
* Complainant Address
* Complainant Phone
* Method of complaint
* Product Code
* Complaint Description
* Investigated by
* Complaint Cause
* Corrective action
* Date of corrective action completion
* Date of reply to customer
* Attached Documents

### GLO 01 Glass Audit

#### Description

Monthly Glass Audit

#### Fields

* Date
* Author
* Area
* Product Type
* Amount
* Amount broken
* Action taken

### GLO 02 Glass Breakage Report

#### Fields

* Date
* Author
* Area
* Details
* Area cleared and food disposed?

### INT 01 Intake of goods

#### Fields

Formset:

* Date
* Product
* Batch Code
* Condition
* Supplier
* Accept, hold, reject
* Recipient

### PLA 01 Plaster Log

#### Fields

* Datetime applied
* Plaster recipient
* Plaster in tact at end of shift
* Time checked
* Checked by

### NC 01 Non conformance log

#### Fields

* Author
* Date
* Number
* Nature of non conformance
* Corrective action taken
* Date of close
* Author of close out
* Preventative action taken

### ST 01 Pre employment health questionnaire

#### Fields

 * Attached doc

### ST 02 Return to work questionnaire

#### Fields

 * Attached doc

### ST 03 Staff Induction Programme

#### Fields

 * Attached doc

### ST 04 Training Record

#### Fields

 * Attached doc

### SUP 01 Raw Materials Supplier/ SUP 02 Packaging Supplier/ SUP 03 Services Supplier

#### Fields

 * Date
 * Author
 * Name
 * Address
 * Phone
 * Product
 * Allergies Present
 * Spec present
 * Satisfactory

### TRA 01 - Annex

#### Fields

 * Date
 * Author
 * Date of infusion
 * Ingredients (Formset)
 * * Product
 * * Quantity
 * Date of infusion/sous-vide
 * Date of bottling
 * Best before
 * Yield
 * Yield bottle breakdown (Formset)
 * * Bottle
 * * Cap
 * * Amount
 * Number of breakages
 * Number of bottles
 * Comments

## Models

### User

 * Name
 * Date created
 * Address details
 * > Documents

### Product

 * Name
 * Ingredients

### Document

 * Author (User)
 * Date uploaded
 * Form
 * User

### Form

 * Author (User)
 * Date
 * > Documents

### Complaint(Form)

 * Reason [Bacteria, Packaging, Foreign Body, Other]
 * Products > []
 * Total stock effected

### Complaint(Form)

 * Type [Food safety, specification]
 * Complainant Name
 * Complainant Address
 * Complainant Phone
 * Product
 * Method of complaint
 * Complaint Description
 * Investigated by user (User)
 * Complaint Cause
 * Corrective action
 * Date of corrective action completion
 * Date of reply to customer

### Glass Audit (Form)

 * Area (Area)
 * Product Type