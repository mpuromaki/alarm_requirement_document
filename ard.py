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
        <title>ARD: {{ ard_id }}</title>
    </head>
    <body>
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

    # Process ARD data

    # Return rendered results page
    return render_template_string(
        RESULT_HTML,
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