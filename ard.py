# -----------------------------------------------------------------------------
# ALARM REQUIREMENT DOCUMENT (ARD) TOOL
# Simple web-based one-file application for generating alarm requirement
# documents.
# -----------------------------------------------------------------------------

from flask import Flask, request, render_template_string
import logging
import sys

# -----------------------------------------------------------------------------
# INTERNAL TOOLING
# -----------------------------------------------------------------------------

# Silence logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
flask_log = logging.getLogger('flask.app')
flask_log.setLevel(logging.ERROR)

# Create the web application
app = Flask(__name__)

def disable_stdout():
    f = sys.stdout = open('/dev/null', 'w')
    sys.stdout = f
    sys.stderr = f

def enable_stdout():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

def print(*args, **kwargs):
    enable_stdout()
    __builtins__.print(*args, **kwargs)
    disable_stdout()

def generate_random_id():
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# -----------------------------------------------------------------------------
# HTML TEMPLATES
# -----------------------------------------------------------------------------

INPUT_HTML = """
<!doctype html>
<html>
    <head>
        <title>Alarm Requirement Document</title>
        <meta charset="utf-8">
        <style>
            /* PAGE STYLING */
            page {
                display: block;
                max-width: 900px;
                margin: 20px auto;
                padding: 20px;
                box-sizing: border-box;
                background-color: #f9f9f9;
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                font-family: Arial, sans-serif;
            }

            hr {
                margin-top: 10px;
                margin-bottom: 20px;
            }

            /* GENERIC INPUT FIELD STYLING */
            input[type="text"] {
                width: 100%;
                box-sizing: border-box;
                margin-bottom: 10px;
                padding: 6px;
            }

            textarea {
                field-sizing: content;
                min-width: 100%;
                min-height: 80px;
            }

            /* IMPACT ROW STYLING */
            .impact-row {
                display: grid;
                grid-template-columns: 220px 1fr;
                align-items: center;
                margin-bottom: 15px;
            }

            .impact-info {
                margin-right: 10px;
            }

            .impact-info .impact-desc {
                font-size: 0.85em;
                color: #666;
            }

            .impact-row .grid {
                display: grid;
                grid-auto-flow: column;
                grid-auto-columns: 1fr;
                gap: 5px;
            }

            .impact-row .grid .cell {
                padding: 10px;
                text-align: center;
                background-color: GhostWhite;
                color: Black;
                cursor: pointer;
                border: 1px solid black;
                border-radius: 5px;
                user-select: none;
                transition: background-color 0.2s, color 0.2s;
            }

            .impact-row .grid .cell:hover {
                background-color: LightGray;
                color: Black;
            }

            .impact-row .grid .cell.selected {
                background-color: LightGreen;
                color: #000;
            }

            /* BOOLEAN ROW STYLING */
            .boolean-row {
                display: grid;
                grid-template-columns: 1fr 220px;
                align-items: center;
                margin-bottom: 15px;
            }

            .boolean-info {
                margin-right: 10px;
            }

            .boolean-info .boolean-desc {
                font-size: 0.85em;
                color: #666;
            }

            .boolean-row .grid {
                display: grid;
                grid-auto-flow: column;
                grid-auto-columns: 1fr;
                gap: 5px;
                justify-items: end;
            }

            .boolean-row .grid .cell {
                padding: 10px;
                text-align: center;
                background-color: GhostWhite;
                color: Black;
                cursor: pointer;
                border: 1px solid black;
                border-radius: 5px;
                user-select: none;
                width: 80px;
                transition: background-color 0.2s, color 0.2s;
            }

            .boolean-row .grid .cell:hover {
                background-color: LightGray;
                color: Black;
            }

            .boolean-row .grid .cell.selected {
                background-color: LightGreen;
                color: #000;
            }

            /* Submit buttons */
            #results {
                display: grid;
                grid-template-columns: auto 1fr auto;
                gap: 10px;
                width: 100%;
            }

            #results input[type="submit"] {
                padding: 8px 16px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <page>
            <h1>Alarm Requirement Document</h1>

            <p>Alarm Requirement Document (ARD) is a document to capture the requirements for a specific
            alarm. These are used as a low-friction way to get stakeholders to participate in the
            alarm design process. The ARD captures key information about an alarm from business and
            operations perspective. It is not intended to record any technical details.</p>

            <h3>What is an alarm?</h3>
            <p>An alarm is a prioritized notification meant to draw attention and require action from
            operators.</p>
            <p>Requirements for alarms:</p>
            <ol>
                <li>Actionable. Alarm requires operator action to resolve.</li>
                <li>Prioritized. Alarms' priority is defined by impact and response time.</li>
                <li>Documented. Reaction to alarm is documented and available to operators.</li>
                <li>Prominent. Alarms are visible until operators acknowledge them.</li>
            </ol>

            <form id="ard" method="post" action="/results">
                <hr/>
                <h2>Alarm Information</h2>

                <label>Alarm Requirement ID:</label>
                <input name="ard_id" id="ard_id" type="text" value="{{ ard_id }}"><br>

                <label>Alarm Requirement Title:</label>
                <input name="ard_title" id="ard_title" type="text" placeholder="Connection lost between systems A and B"><br>

                <label>Affected Systems:</label>
                <input name="ard_systems" id="ard_systems" type="text" placeholder="System A, System B"><br>

                <label>Description of the alarm functionality:</label><br>
                <textarea name="ard_description" id="ard_description" rows="4" placeholder="There is no connectivity between systems A and B."></textarea><br>

                <label>Description of the impact if not mitigated:</label><br>
                <textarea name="ard_impact" id="ard_impact" rows="4" placeholder="Critical business process X is stopped when this connection is down."></textarea><br>

                <label>Required operator response:</label><br>
                <textarea name="ard_response" id="ard_response" rows="4" placeholder="Require Major Incident Response and enact manual backup procedure Y."></textarea><br>

                <hr/>
                <h2>Priority Analysis</h2>

                <!-- Operator Reaction Time -->
                <div class="impact-row">
                    <div class="impact-info">
                        <strong>Reaction Time</strong>
                        <div class="impact-desc">Time within which operator must respond</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="0">Now</div>
                        <div class="cell" data-value="1">Within 15 minutes</div>
                        <div class="cell" data-value="2">Within 1 hour</div>
                        <div class="cell" data-value="3">Within 4 hours</div>
                        <div class="cell" data-value="4">No action</div>
                    </div>
                    <input type="hidden" name="ard_reaction_time" value="">
                </div>

                <!-- Operability Impact -->
                <div class="impact-row">
                    <div class="impact-info">
                        <strong>Operability Impact</strong>
                        <div class="impact-desc">Effect on system operation</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="0">Rebuild required</div>
                        <div class="cell" data-value="1">Lost production</div>
                        <div class="cell" data-value="2">Reduced capability</div>
                        <div class="cell" data-value="3">Reduced efficiency</div>
                        <div class="cell" data-value="4">No effect</div>
                    </div>
                    <input type="hidden" name="ard_operability_impact" value="">
                </div>

                <!-- Business Impact -->
                <div class="impact-row">
                    <div class="impact-info">
                        <strong>Business Impact</strong>
                        <div class="impact-desc">Financial consequences</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="0">Existential</div>
                        <div class="cell" data-value="1">Major financial loss</div>
                        <div class="cell" data-value="2">Moderate financial loss</div>
                        <div class="cell" data-value="3">Neglible financial loss</div>
                        <div class="cell" data-value="4">No effect</div>
                    </div>
                    <input type="hidden" name="ard_business_impact" value="">
                </div>

                <!-- Safety Impact -->
                <div class="impact-row">
                    <div class="impact-info">
                        <strong>Safety Impact</strong>
                        <div class="impact-desc">Potential for injury or harm</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="0">Life-threatening</div>
                        <div class="cell" data-value="1">Major injury</div>
                        <div class="cell" data-value="2">Minor injury</div>
                        <div class="cell" data-value="3">Near miss</div>
                        <div class="cell" data-value="4">No effect</div>
                    </div>
                    <input type="hidden" name="ard_safety_impact" value="">
                </div>

                <!-- Security Impact -->
                <div class="impact-row">
                    <div class="impact-info">
                        <strong>Security Impact</strong>
                        <div class="impact-desc">Impact on security / unauthorized access</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="0">Existential</div>
                        <div class="cell" data-value="1">Breach</div>
                        <div class="cell" data-value="2">Suspicious activity</div>
                        <div class="cell" data-value="3">Policy violation</div>
                        <div class="cell" data-value="4">No effect</div>
                    </div>
                    <input type="hidden" name="ard_security_impact" value="">
                </div>

                <!-- Environmental Impact -->
                <div class="impact-row">
                    <div class="impact-info">
                        <strong>Environmental Impact</strong>
                        <div class="impact-desc">Effect on environment</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="0">Permanent Major damage</div>
                        <div class="cell" data-value="1">Extended damage</div>
                        <div class="cell" data-value="2">Contained damage</div>
                        <div class="cell" data-value="3">Minor effect</div>
                        <div class="cell" data-value="4">No effect</div>
                    </div>
                    <input type="hidden" name="ard_environmental_impact" value="">
                </div>

                <hr/>
                <h2>Feasibility Analysis</h2>
                
                <!-- Operator Actionability -->
                <fieldset class="boolean-row">
                    <div class="boolean-info">
                        <strong>Operator Actionability</strong>
                        <div class="boolean-desc">Can the operator take direct action to resolve the alarm condition?</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="true">Yes</div>
                        <div class="cell" data-value="false">No</div>
                    </div>
                    <input type="hidden" name="ard_operator_actionability" value="">
                </fieldset>

                <!-- Automation Potential -->
                <fieldset class="boolean-row">
                    <div class="boolean-info">
                        <strong>Automation Potential</strong>
                        <div class="boolean-desc">Could the system automatically detect and implement that operator action to resolve the alarm condition?</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="true">Yes</div>
                        <div class="cell" data-value="false">No</div>
                    </div>
                    <input type="hidden" name="ard_automation_potential" value="">
                </fieldset>

                <!-- State Dependency -->
                <fieldset class="boolean-row">
                    <div class="boolean-info">
                        <strong>State Dependency</strong>
                        <div class="boolean-desc">Does the alarm condition depend on the state of the system? Are there situations, control modes or signals which should disable this alarm?</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="true">Yes</div>
                        <div class="cell" data-value="false">No</div>
                    </div>
                    <input type="hidden" name="ard_state_dependency" value="">
                </fieldset>

                <!-- Alarm Frequency Risk -->
                <fieldset class="boolean-row">
                    <div class="boolean-info">
                        <strong>Alarm Frequency Risk</strong>
                        <div class="boolean-desc">Could this alarm occur multiple times per shift?</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="true">Yes</div>
                        <div class="cell" data-value="false">No</div>
                    </div>
                    <input type="hidden" name="ard_frequency_risk" value="">
                </fieldset>

                <!-- Alarm Flood Risk -->
                <fieldset class="boolean-row">
                    <div class="boolean-info">
                        <strong>Alarm Flood Risk</strong>
                        <div class="boolean-desc">Could this alarm occur or change state repeatedly in short time?</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="true">Yes</div>
                        <div class="cell" data-value="false">No</div>
                    </div>
                    <input type="hidden" name="ard_flood_risk" value="">
                </fieldset>

                <!-- Alarm Chattering Risk -->
                <fieldset class="boolean-row">
                    <div class="boolean-info">
                        <strong>Alarm Chattering Risk</strong>
                        <div class="boolean-desc">Could this alarm occur or change state repeatedly in short time?</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="true">Yes</div>
                        <div class="cell" data-value="false">No</div>
                    </div>
                    <input type="hidden" name="ard_chattering_risk" value="">
                </fieldset>

                <hr/>
                <div id="results">
                    <input type="submit" value="Delete">
                    <div></div>
                    <input type="submit" value="Generate">
                </div>
            </form>
        </page>

        <script>
            // Handle cell selection for all impact rows
            document.querySelectorAll('.impact-row').forEach(row => {
                const hiddenInput = row.querySelector('input[type="hidden"]');
                if (!hiddenInput) return;
                row.querySelectorAll('.cell').forEach(cell => {
                    cell.addEventListener('click', () => {
                        row.querySelectorAll('.cell').forEach(c => c.classList.remove('selected'));
                        cell.classList.add('selected');
                        hiddenInput.value = cell.dataset.value;
                    });
                });
            });
            document.querySelectorAll('.boolean-row').forEach(row => {
                const hiddenInput = row.querySelector('input[type="hidden"]');
                if (!hiddenInput) return;
                row.querySelectorAll('.cell').forEach(cell => {
                    cell.addEventListener('click', () => {
                        row.querySelectorAll('.cell').forEach(c => c.classList.remove('selected'));
                        cell.classList.add('selected');
                        hiddenInput.value = cell.dataset.value;
                    });
                });
            });
        </script>
    </body>
</html>
"""

RESULT_HTML = """
<!doctype html>
<html>
	<head>
		<title>ARD{{ ard_id }}</title>
		<meta charset="utf-8">

		<style>

			body {
				font-family: Arial, sans-serif;
				background: #eee;
				padding: 20px;
			}

			page {
				display: block;
				width: 900px;
				margin: auto;
				padding: 40px;
				background: white;
				box-shadow: 0 0 8px rgba(0,0,0,0.15);
				box-sizing: border-box;
			}

			/* HEADER */

            .header {
                display: grid;
                grid-template-columns: 1fr auto;
                grid-template-rows: 1fr 1fr auto;
                margin-bottom: 20px;
                border-top: 1px solid #ccc;
                border-bottom: 1px solid #ccc;
                padding-top: 10px;
                padding-bottom: 10px;
            }

            .header h1 {
                margin-top: 5px;
                margin-bottom: 5px;
                font-size: 28px;
                color: #111;
            }

            .header p {
                margin: 0;
                color: #333;
            }

			.id-container {
				font-size: 18px;
				color: #555;
                align-content: center;
			}

            /* PRIORITY ICON SYSTEM */

            #priority-container {
                width: 110px;
                height: 110px;
                grid-column: 2;
                grid-row: 1 / span 3;
            }

            #priority-container > div {
                width: 100%;
                height: 100%;

                background-size: contain;
                background-repeat: no-repeat;
                background-position: center;
            }

            /* PRIORITY 0 — RED SQUARE */

            #priority-0 {
            background-image: url("data:image/svg+xml;utf8,\
            <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>\
            <rect x='5' y='5' width='90' height='90' fill='%23ff3b30' stroke='black' stroke-width='5'/>\
            <text x='50' y='68' font-size='52' text-anchor='middle' font-family='Arial' font-weight='bold'>0</text>\
            </svg>");
            }

            /* PRIORITY 1 — TRIANGLE UP */

            #priority-1 {
            background-image: url("data:image/svg+xml;utf8,\
            <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>\
            <polygon points='50,5 95,95 5,95' fill='%23ffd84d' stroke='black' stroke-width='5'/>\
            <text x='50' y='78' font-size='48' text-anchor='middle' font-family='Arial' font-weight='bold'>1</text>\
            </svg>");
            }


            /* PRIORITY 2 — TRIANGLE DOWN */

            #priority-2 {
            background-image: url("data:image/svg+xml;utf8,\
            <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>\
            <polygon points='5,5 95,5 50,95' fill='%23d08a52' stroke='black' stroke-width='5'/>\
            <text x='50' y='50' font-size='48' text-anchor='middle' font-family='Arial' font-weight='bold'>2</text>\
            </svg>");
            }


            /* PRIORITY 3 — DIAMOND */

            #priority-3 {
            background-image: url("data:image/svg+xml;utf8,\
            <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>\
            <polygon points='50,5 95,50 50,95 5,50' fill='%23b96a9e' stroke='black' stroke-width='5'/>\
            <text x='50' y='66' font-size='48' text-anchor='middle' font-family='Arial' font-weight='bold'>3</text>\
            </svg>");
            }


            /* PRIORITY 4 — NOT AN ALARM */

            #priority-4 {
            background-image: url("data:image/svg+xml;utf8,\
            <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>\
            <rect x='5' y='5' width='90' height='90' fill='white' stroke='%23888' stroke-width='4' stroke-dasharray='6,4'/>\
            <text x='50' y='48' font-size='14' text-anchor='middle' font-family='Arial' font-weight='bold'>NOT AN</text>\
            <text x='50' y='66' font-size='16' text-anchor='middle' font-family='Arial' font-weight='bold'>ALARM</text>\
            </svg>");
            }

			/* CONTENT SECTIONS */

			.section {
				margin-bottom: 20px;
			}

			.section-title {
				font-weight: bold;
				font-size: 14px;
				text-transform: uppercase;
				letter-spacing: 1px;
				color: #111;
				border-bottom: 1px solid #ccc;
				margin-bottom: 6px;
				padding-bottom: 3px;
			}

			.section-content {
				font-size: 14px;
				line-height: 1.5;
				white-space: pre-wrap;
			}

			/* IMPLEMENTATION GUIDANCE */

			.guidance {
				background: #fafafa;
				border: 1px dashed #bbb;
				padding: 12px;
				margin-top: 25px;
			}

			.guidance ul {
				margin: 5px 0 0 18px;
			}

			/* FOOTNOTE */

			.footnote {
				margin-top: 30px;
				padding-top: 10px;
				border-top: 1px solid #ddd;
				font-size: 12px;
				color: #666;
			}

            .footnote h2 {
                grid-column: span 2;
                margin-top: 0px;
            }

			.footnote-grid {
				display: grid;
				grid-template-columns: 1fr 1fr;
				gap: 6px 20px;
				margin-top: 5px;
			}

            .footnote-left {
                grid-column: 1;
                display: grid;
                grid-template-columns: auto 60px;
            }

            .footnote-right {
                grid-column: 2;
                display: grid;
                grid-template-columns: auto 60px;
            }

			.footnote-label {
				font-weight: bold;
				color: #444;
			}

			/* PRINT FRIENDLY */

			@media print {

				body {
					background: none;
					padding: 0;
				}

				page {
					box-shadow: none;
					margin: 0;
					width: auto;
				}

			}

		</style>

	</head>

	<body>

		<page>

			<div class="header">
				
                <div class="id-container">
					ARD{{ ard_id }}
				</div>
				
                <div id="priority-container">
                    <div id="priority-{{ calculated_priority }}"></div>
                </div>


			    <h1>{{ ard_title }}</h1>
                <p>Affects: {{ ard_systems }}</p>
			</div>

			<div class="section">

				<div class="section-title">
					Alarm Description
				</div>

				<div class="section-content">
                    {{ ard_description }}
				</div>

			</div>


			<div class="section">

				<div class="section-title">
					Impact if Not Mitigated
				</div>

				<div class="section-content">
                    {{ ard_impact }}
				</div>

			</div>


			<div class="section">

				<div class="section-title">
					Required Operator Response
				</div>

				<div class="section-content">
                    {{ ard_response }}
				</div>

			</div>


			<div class="guidance">

				<div class="section-title">
					Implementation Guidance
				</div>

				<ul>
					{% for note in implementation_notes %}
					<li>{{ note }}</li>
					{% endfor %}
				</ul>

			</div>

			<div class="footnote">
				<div class="footnote-grid">
                    <div class="footnote-left">
                        <h2>Priority Analysis</h2>

                        <div class="footnote-label">Reaction Time</div>
                        <div>{{ ard_reaction_time }}</div>

                        <div class="footnote-label">Operability Impact</div>
                        <div>{{ ard_operability_impact }}</div>

                        <div class="footnote-label">Business Impact</div>
                        <div>{{ ard_business_impact }}</div>

                        <div class="footnote-label">Safety Impact</div>
                        <div>{{ ard_safety_impact }}</div>

                        <div class="footnote-label">Security Impact</div>
                        <div>{{ ard_security_impact }}</div>

                        <div class="footnote-label">Environmental Impact</div>
                        <div>{{ ard_environmental_impact }}</div>
                    </div>
                    <div class="footnote-right">
                        <h2>Feasibility Analysis</h2>

                        <div class="footnote-label">Operator Actionability</div>
                        <div>{{ ard_operator_actionability }}</div>

                        <div class="footnote-label">Automation Potential</div>
                        <div>{{ ard_automation_potential }}</div>

                        <div class="footnote-label">State Dependency</div>
                        <div>{{ ard_state_dependency }}</div>

                        <div class="footnote-label">Frequency Risk</div>
                        <div>{{ ard_frequency_risk }}</div>

                        <div class="footnote-label">Flood Risk</div>
                        <div>{{ ard_flood_risk }}</div>

                        <div class="footnote-label">Chattering Risk</div>
                        <div>{{ ard_chattering_risk }}</div>
                    </div>

				</div>

			</div>

		</page>

	</body>

</html>
"""

# -----------------------------------------------------------------------------
# WEBSERVER FUNCTIONALITY
# -----------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def form():
    # Return the input form page
    return render_template_string(INPUT_HTML,
                                  ard_id=generate_random_id())

@app.route("/results", methods=["POST"])
def results():
    # Gather ARD data from form
    # - General Information
    ard_id = request.form.get("ard_id")
    ard_title = request.form.get("ard_title")
    ard_systems = request.form.get("ard_systems")

    # - ARD Content
    ard_description = request.form.get("ard_description")
    ard_impact = request.form.get("ard_impact")
    ard_response = request.form.get("ard_response")

    # - Priority Analysis
    ard_reaction_time = request.form.get("ard_reaction_time")
    ard_operability_impact = request.form.get("ard_operability_impact")
    ard_business_impact = request.form.get("ard_business_impact")
    ard_safety_impact = request.form.get("ard_safety_impact")
    ard_security_impact = request.form.get("ard_security_impact")
    ard_environmental_impact = request.form.get("ard_environmental_impact")

    # - Feasibility Analysis
    ard_operator_actionability = request.form.get("ard_operator_actionability")
    ard_automation_potential = request.form.get("ard_automation_potential")
    ard_state_dependency = request.form.get("ard_state_dependency")
    ard_frequency_risk = request.form.get("ard_frequency_risk")
    ard_flood_risk = request.form.get("ard_flood_risk")
    ard_chattering_risk = request.form.get("ard_chattering_risk")

    # Process ARD data

    # Return rendered results page
    return render_template_string(
        RESULT_HTML,
        ard_id=ard_id,
        ard_title=ard_title,
        ard_systems=ard_systems,
        ard_description=ard_description,
        ard_impact=ard_impact,
        ard_response=ard_response,
        ard_reaction_time=ard_reaction_time,
        ard_operability_impact=ard_operability_impact,
        ard_business_impact=ard_business_impact,
        ard_safety_impact=ard_safety_impact,
        ard_security_impact=ard_security_impact,
        ard_environmental_impact=ard_environmental_impact,
        ard_operator_actionability=ard_operator_actionability,
        ard_automation_potential=ard_automation_potential,
        ard_state_dependency=ard_state_dependency,
        ard_frequency_risk=ard_frequency_risk,
        ard_flood_risk=ard_flood_risk,
        ard_chattering_risk=ard_chattering_risk,
        calculated_priority=0,  # Placeholder, implement priority calculation logic here
    )

# -----------------------------------------------------------------------------
# APPLICATION ENTRY POINT
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    disable_stdout()
    print("-----------------------------------------------------")
    print("Alarm Requirement Document ==> http://localhost:62682")
    print("-----------------------------------------------------")
    app.run(port=62682, debug=False, use_reloader=False)