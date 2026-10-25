"""Scenario data. Each option has a stable id (A-D), a behaviour 'key' and internal game tags (not diagnoses)."""
_R = [
 ("money", "You find ₹500 in an old jacket. What's the move?", [("💾","Save it for later","save","cautious patient"),("🍕","Order something delicious","treat","spontaneous comfort_seeking"),("🛍️","Buy something completely unnecessary","splurge","impulsive novelty_seeking"),("🤝","Give it to someone who needs it","give","generous")]),
 ("money", "You suddenly receive ₹10,000.", [("💾","Save most of it","save","cautious patient"),("📈","Invest some of it","invest","analytical organised"),("🎉","Spend it on something fun","splurge","impulsive novelty_seeking"),("📚","Learn a new skill with it","learn","organised novelty_seeking")]),
 ("money", "Two phones, same price. How do you pick?", [("📊","Read every review","research","analytical patient"),("✨","Whichever looks cooler","vibe","impulsive"),("💬","Ask friends","ask","social"),("🪙","Flip a coin","coin","spontaneous")]),
 ("lifestyle", "You have an entire Sunday with zero responsibilities.", [("🛋️","Stay home and recharge","home","comfort_seeking independent"),("🧭","Go outside and explore","explore","adventurous novelty_seeking"),("🧑‍🤝‍🧑","Meet friends","friends","social"),("🛠️","Start a random new project","project","spontaneous novelty_seeking")]),
 ("lifestyle", "Your alarm rings on a cold morning.", [("⏰","Get up immediately","up","organised"),("😴","Snooze for five minutes","snooze","comfort_seeking"),("🛌","Snooze until reality becomes optional","snooze","comfort_seeking impulsive"),("📱","Wake up and start scrolling","scroll","spontaneous")]),
 ("lifestyle", "Plans get cancelled at the last minute.", [("🏠","Delighted. Staying in.","home","comfort_seeking independent"),("🚀","Make new plans right now","friends","spontaneous social"),("📝","Finish something useful","project","organised independent"),("🎬","Rewatch a comfort show","home","comfort_seeking patient")]),
 ("lifestyle", "Movie night. What do you put on?", [("🔁","Something you've seen five times","home","comfort_seeking cautious"),("🆕","A totally unknown film","explore","novelty_seeking adventurous"),("🍿","Whatever the group picks","friends","social"),("📖","Skip it and read a book","project","independent patient")]),
 ("people", "Someone sends you 'we need to talk'.", [("💬","Ask what happened immediately","ask","social analytical"),("🌀","Overthink every possible scenario","overthink","analytical cautious"),("🙈","Ignore it for a while","ignore","independent"),("😎","Reply like nothing is wrong","chill","patient")]),
 ("people", "A friend proposes a road trip tonight.", [("🚗","Pack and go","go","adventurous spontaneous"),("🗺️","Ask for a plan first","plan","organised cautious"),("🙅","Politely decline","home","comfort_seeking independent"),("🔧","Suggest a better route and date","plan","analytical social")]),
 ("risk", "You're at the top of a zip-line.", [("🪂","Jump immediately","go","adventurous impulsive"),("👀","Watch two more people first","watch","cautious patient"),("🧮","Ask about the safety record","research","analytical"),("🚶","Climb back down","home","cautious comfort_seeking")]),
 ("work", "A deadline is three days away.", [("🏁","Start right now","now","organised"),("🔥","Wait for last-night adrenaline","last","impulsive"),("🗓️","Split it into small chunks","plan","patient analytical"),("🤝","Ask for help early","ask","social")]),
 ("food", "A new restaurant has a huge menu.", [("🍛","Order your usual","usual","cautious comfort_seeking"),("🌶️","Pick the weirdest item","explore","novelty_seeking adventurous"),("🍽️","Share a bunch with the table","friends","social generous"),("🔎","Read reviews before ordering","research","analytical")]),
]
SCENARIOS = [{"id": f"s{i:02d}", "category": c, "text": q,
  "options": [{"id": "ABCD"[j], "emoji": e, "text": t, "key": k, "tags": g.split()} for j, (e, t, k, g) in enumerate(o)]}
  for i, (c, q, o) in enumerate(_R, 1)]
BY_ID = {s["id"]: s for s in SCENARIOS}
def option(sc, oid):
    return next((o for o in sc["options"] if o["id"] == oid), None)
def public(sc):
    return {"id": sc["id"], "category": sc["category"], "text": sc["text"],
            "options": [{"id": o["id"], "emoji": o["emoji"], "text": o["text"]} for o in sc["options"]]}
