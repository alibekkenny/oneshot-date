"""The wizard content — the date-planning steps and their options.

This is the file to edit when you want to change what she gets to pick.
Each step is a multi-select; `value` is what gets stored & sent to Telegram.
Set "allow_custom": True to give the step a "Something else…" option with a
free-text box (whatever she types is stored & sent too).
"""

STEPS = [
    {
        "key": "entertainment",
        "title": "What should we do?",
        "subtitle": "Pick anything that sounds fun — choose as many as you like.",
        "allow_custom": True,
        "options": [
            {"emoji": "🎬", "label": "Cinema"},
            {"emoji": "🌳", "label": "Walk in the park"},
            {"emoji": "🖼️", "label": "Art exhibition"},
            {"emoji": "🎯", "label": "Shooting range"},
            {"emoji": "🏎️", "label": "Karting"},
            {"emoji": "💬", "label": "Just vibe & talk at a restaurant"},
        ],
    },
    {
        "key": "eating",
        "title": "And to eat?",
        "subtitle": "What are you in the mood for?",
        "allow_custom": True,
        "options": [
            {"emoji": "🍣", "label": "Sushi"},
            {"emoji": "🍝", "label": "Pasta"},
            {"emoji": "🍔", "label": "Burgers"},
            {"emoji": "🥢", "label": "Korean food"},
            {"emoji": "🍕", "label": "Pizza"},
        ],
    },
    {
        "key": "drinking",
        "title": "Something to drink?",
        "subtitle": "The most important question, honestly.",
        "allow_custom": True,
        "options": [
            {"emoji": "☕", "label": "Coffee"},
            {"emoji": "🧋", "label": "Bubble tea"},
            {"emoji": "🍵", "label": "Matcha"},
            {"emoji": "🫖", "label": "Tea"},
        ],
    },
]

# Keys the API & wizard expect to exist. Keep in sync with STEPS above.
STEP_KEYS = [step["key"] for step in STEPS]
