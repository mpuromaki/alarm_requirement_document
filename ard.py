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

            /* FORM INPUTS */
            input[type="text"], textarea {
                width: 100%;
                box-sizing: border-box;
                margin-bottom: 10px;
                padding: 6px;
            }

            /* PRIORITY LEGEND */
            .priority-legend {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                font-size: 0.9em;
                font-style: italic;
                color: #555;
            }

            /* IMPACT ROW GRID */
            .impact-row {
                display: grid;
                grid-template-columns: 220px 1fr;
                align-items: center;
                margin-bottom: 15px;
            }

            /* Left column: title + description */
            .impact-info {
                margin-right: 10px;
            }

            .impact-info .impact-desc {
                font-size: 0.85em;
                color: #666;
            }

            /* Right column: clickable cells grid */
            .impact-row .grid {
                display: grid;
                grid-template-columns: repeat(5, 1fr);
                gap: 5px;
            }

            /* Cells styling */
            .impact-row .grid .cell {
                padding: 10px;
                text-align: center;
                background-color: #444;
                color: #fff;
                cursor: pointer;
                border-radius: 5px;
                user-select: none;
                transition: background-color 0.2s, color 0.2s;
            }

            .impact-row .grid .cell:hover {
                background-color: #666;
            }

            .impact-row .grid .cell.selected {
                background-color: #aaa;
                color: #000;
            }

            /* Submit buttons */
            input[type="submit"] {
                padding: 8px 16px;
                margin-right: 10px;
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
                <h2>General information</h2>

                <label>Alarm Requirement ID:</label>
                <input name="ard_id" id="ard_id" value="{{ ard_id }}" /><br>

                <label>Alarm Requirement Title:</label>
                <input name="ard_title" id="ard_title"><br>

                <label>Description of the alarm functionality:</label><br>
                <textarea name="ard_description" id="ard_description" rows="4" cols="50"></textarea><br>

                <label>Description of the impact if not mitigated:</label><br>
                <textarea name="ard_impact" id="ard_impact" rows="4" cols="50"></textarea><br>

                <label>Required operator response:</label><br>
                <textarea name="ard_response" id="ard_response" rows="4" cols="50"></textarea><br>

                <h2>Prioritization</h2>

                <!-- Priority legend -->
                <div class="priority-legend">
                    <span>Higher impact / higher importance</span>
                    <span>Lower impact / lower importance</span>
                </div>

                <!-- Operator Reaction Time -->
                <div class="impact-row">
                    <div class="impact-info">
                        <strong>Operator Reaction Time</strong>
                        <div class="impact-desc">Time within which operator must respond</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="0">0 - Instant</div>
                        <div class="cell" data-value="1">1 - &lt; 10 min</div>
                        <div class="cell" data-value="2">2 - &lt; 30 min</div>
                        <div class="cell" data-value="3">3 - &lt; 2 hours</div>
                        <div class="cell" data-value="4">4 - During shift</div>
                    </div>
                    <input type="hidden" name="reaction_time" value="">
                </div>

                <!-- Operability Impact -->
                <div class="impact-row">
                    <div class="impact-info">
                        <strong>Operability Impact</strong>
                        <div class="impact-desc">Effect on system operation</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="0">0 - Plant trip</div>
                        <div class="cell" data-value="1">1 - Unit trip</div>
                        <div class="cell" data-value="2">2 - Degraded operation</div>
                        <div class="cell" data-value="3">3 - Reduced efficiency</div>
                        <div class="cell" data-value="4">4 - Minor effect</div>
                    </div>
                    <input type="hidden" name="operability" value="">
                </div>

                <!-- Business Impact -->
                <div class="impact-row">
                    <div class="impact-info">
                        <strong>Business Impact</strong>
                        <div class="impact-desc">Financial consequences</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="0">0 - Major loss</div>
                        <div class="cell" data-value="1">1 - Significant loss</div>
                        <div class="cell" data-value="2">2 - Moderate loss</div>
                        <div class="cell" data-value="3">3 - Minor loss</div>
                        <div class="cell" data-value="4">4 - Negligible</div>
                    </div>
                    <input type="hidden" name="business" value="">
                </div>

                <!-- Safety Impact -->
                <div class="impact-row">
                    <div class="impact-info">
                        <strong>Safety Impact</strong>
                        <div class="impact-desc">Potential for injury or harm</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="0">0 - Life-threatening</div>
                        <div class="cell" data-value="1">1 - Major injury</div>
                        <div class="cell" data-value="2">2 - Minor injury</div>
                        <div class="cell" data-value="3">3 - Near miss</div>
                        <div class="cell" data-value="4">4 - None</div>
                    </div>
                    <input type="hidden" name="safety" value="">
                </div>

                <!-- Security Impact -->
                <div class="impact-row">
                    <div class="impact-info">
                        <strong>Security Impact</strong>
                        <div class="impact-desc">Impact on security / unauthorized access</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="0">0 - Active breach</div>
                        <div class="cell" data-value="1">1 - Confirmed breach</div>
                        <div class="cell" data-value="2">2 - Suspicious activity</div>
                        <div class="cell" data-value="3">3 - Policy violation</div>
                        <div class="cell" data-value="4">4 - None</div>
                    </div>
                    <input type="hidden" name="security" value="">
                </div>

                <!-- Environmental Impact -->
                <div class="impact-row">
                    <div class="impact-info">
                        <strong>Environmental Impact</strong>
                        <div class="impact-desc">Effect on environment</div>
                    </div>
                    <div class="grid">
                        <div class="cell" data-value="0">0 - Major release</div>
                        <div class="cell" data-value="1">1 - Reportable release</div>
                        <div class="cell" data-value="2">2 - Contained spill</div>
                        <div class="cell" data-value="3">3 - Minor release</div>
                        <div class="cell" data-value="4">4 - None</div>
                    </div>
                    <input type="hidden" name="environment" value="">
                </div>

                <input type="submit" value="Delete and start over">
                <input type="submit" value="Generate">
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