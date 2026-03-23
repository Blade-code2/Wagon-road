import json
import random
import time
from Credits import *
from Helpers import *

DEBUG_SKIP_TO_CH2 = True   # Set to False for normal gameplay

# ---------------- FILE STATE SYSTEM ----------------

def ensure_game_data():
    if not os.path.exists(GAME_DATA_DIR):
        os.makedirs(GAME_DATA_DIR)


def default_state():
    return {
        "mara_erased": False,
        "jon_erased": False,
        "eli_erased": False,
        "mara_img_viewed": False,
        "jon_img_viewed": False,
        "eli_img_viewed": False,
        "suppressor_deleted": False,
        "hunter_intensity": 0,
        "horror_turns": 0
    }


def load_state():
    ensure_game_data()
    if not os.path.exists(STATE_FILE):
        state = default_state()
        save_state(state)
        return state
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        state = default_state()
        save_state(state)
        return state


def save_state(state):
    ensure_game_data()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def create_initial_files():
    ensure_game_data()
    # NPC files
    for name, path in NPC_FILES.items():
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(f"passenger={name}\nstatus=ok\n")
    # Suppressor file
    if not os.path.exists(SUPPRESSOR_FILE):
        with open(SUPPRESSOR_FILE, "w") as f:
            f.write("entity_suppressor=active\n")


def check_npc_files(state):
    """Update state based on NPC files being deleted or renamed to .img."""
    for name, base_path in NPC_FILES.items():
        mem_exists = os.path.exists(base_path)
        img_path = os.path.splitext(base_path)[0] + ".img"
        img_exists = os.path.exists(img_path)

        key_erased = f"{name.lower()}_erased"
        key_img = f"{name.lower()}_img_viewed"

        # If .img exists, treat as "player tried to see remains"
        if img_exists:
            state[key_img] = True
            state[key_erased] = True  # seat empty in-game

        # If neither mem nor img exists, treat as erased
        if not mem_exists and not img_exists:
            state[key_erased] = True

    return state


def check_suppressor_file(state):
    if not os.path.exists(SUPPRESSOR_FILE):
        state["suppressor_deleted"] = True
    return state


# ---------------- NPC CONVERSATIONS ----------------

class NPC:
    def __init__(self, name):
        self.name = name
        self.topics_seen = set()

    def get_topics(self):
        topics = []
        if "family" not in self.topics_seen:
            topics.append(("Ask about their family", "family"))
        if "road" not in self.topics_seen:
            topics.append(("Ask about the road", "road"))
        if "bridge" not in self.topics_seen:
            topics.append(("Ask about the bridge", "bridge"))
        if "feeling" not in self.topics_seen:
            topics.append(("Ask how they're feeling", "feeling"))
        topics.append(("Say nothing and sit with them", "quiet"))
        topics.append(("Leave the conversation", "leave"))
        return topics

    def respond(self, topic_key):
        self.topics_seen.add(topic_key)
        if topic_key == "family":
            return (
                f"{self.name} talks quietly about people they used to travel with.\n"
                "They can't remember all the details, but they smile anyway."
            )
        if topic_key == "road":
            return (
                f"{self.name} says the road feels longer than it should.\n"
                "\"It always does,\" they add."
            )
        if topic_key == "bridge":
            return (
                f"{self.name} glances ahead.\n"
                "\"They say the bridge is old, but it holds. Usually.\""
            )
        if topic_key == "feeling":
            return (
                f"{self.name} admits they're tired, but they'll manage.\n"
                "\"It's just a road,\" they say. \"It has to end somewhere.\""
            )
        if topic_key == "quiet":
            return (
                f"You sit with {self.name} in silence.\n"
                "The wagon creaks. The road hums beneath the wheels."
            )
        if topic_key == "leave":
            return "You stand up and move away from the seat."
        return ""


def run_npc_conversation(npc: NPC, message_log):
    running = True
    last_response = ""
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill(BG_COLOR_NORMAL)
        draw_minimap(screen, 0)

        draw_text(screen, f"You sit beside {npc.name}.", font_main, TEXT_COLOR, LEFT_COL, 70)

        topics = npc.get_topics()
        menu_lines = []
        for i, (label, key) in enumerate(topics, start=1):
            menu_lines.append(f"[{i}] {label}")
        menu_text = "What do you say?\n" + "\n".join(menu_lines)
        draw_text(screen, menu_text, font_small, TEXT_COLOR, LEFT_COL, 120)

        if last_response:
            draw_text(screen, last_response, font_small, TEXT_COLOR_DIM, RIGHT_COL, 120)

        log_y = BOTTOM_LOG_Y
        for i, msg in enumerate(message_log[-3:]):
            draw_text(screen, msg, font_small, TEXT_COLOR_DIM, LEFT_COL, log_y + i * 24)

        draw_scanlines(screen)
        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                idx = event.key - pygame.K_1
                if 0 <= idx < len(topics):
                    label, key = topics[idx]
                    if key == "leave":
                        return
                    last_response = npc.respond(key)


# ---------------- OREGON-STYLE SURVIVAL PHASE ----------------

def run_oregon_phase():
    day = 1
    distance = 0
    food = 120
    water = 120
    wagon = 100
    party_health = 100

    npcs = [NPC("Mara"), NPC("Jon"), NPC("Eli")]

    message_log = [
        "You begin your journey toward the old bridge.",
        "The wagon is loaded. A few quiet passengers ride with you."
    ]

    def add_message(msg):
        nonlocal message_log
        message_log.append(msg)
        if len(message_log) > MAX_LOG_LINES:
            message_log = message_log[-MAX_LOG_LINES:]

    def check_death():
        if party_health <= 0:
            return "Your party collapses from exhaustion and injury."
        if wagon <= 0:
            return "The wagon finally gives out. The wheels splinter and the axle snaps."
        if food <= 0 and water <= 0:
            return "With no food or water left, the journey ends quietly on the side of the road."
        return None

    def travel_event():
        nonlocal food, water, wagon, party_health
        roll = random.random()
        if roll < 0.10:
            loss = random.randint(10, 20)
            food = max(0, food - loss)
            return f"A crate tips over on a bump. You lose {loss} food."
        elif roll < 0.20:
            loss = random.randint(10, 20)
            water = max(0, water - loss)
            return f"A barrel leaks slowly. You lose {loss} water."
        elif roll < 0.30:
            dmg = random.randint(10, 20)
            wagon = max(0, wagon - dmg)
            return f"The wagon hits a deep rut. Wagon condition -{dmg}."
        elif roll < 0.40:
            dmg = random.randint(10, 20)
            party_health = max(0, party_health - dmg)
            return f"The heat wears everyone down. Party health -{dmg}."
        elif roll < 0.45:
            dmg = random.randint(15, 25)
            party_health = max(0, party_health - dmg)
            return f"A passenger falls and is badly hurt. Party health -{dmg}."
        elif roll < 0.50:
            dmg = random.randint(15, 25)
            wagon = max(0, wagon - dmg)
            return f"A wheel cracks on a rock. Wagon condition -{dmg}."
        elif roll < 0.55:
            gain = random.randint(10, 20)
            food += gain
            return f"You find wild berries along the road. Food +{gain}."
        elif roll < 0.60:
            gain = random.randint(10, 20)
            water += gain
            return f"You find a clear stream. Water +{gain}."
        else:
            return "The day passes without incident."

    def rest_event():
        nonlocal party_health, food, water
        gain = random.randint(10, 20)
        party_health = min(100, party_health + gain)
        food = max(0, food - random.randint(3, 7))
        water = max(0, water - random.randint(3, 7))
        return f"You rest for the day. Party health +{gain}."

    def hunt_event():
        nonlocal food, party_health
        roll = random.random()
        if roll < 0.6:
            gain = random.randint(15, 30)
            food += gain
            return f"You hunt along the roadside and bring back {gain} food."
        else:
            dmg = random.randint(5, 15)
            party_health = max(0, party_health - dmg)
            return f"The hunt goes badly. Someone is hurt. Party health -{dmg}."

    def water_search_event():
        nonlocal water, party_health
        roll = random.random()
        if roll < 0.6:
            gain = random.randint(15, 30)
            water += gain
            return f"You find a small stream and refill. Water +{gain}."
        else:
            dmg = random.randint(5, 15)
            party_health = max(0, party_health - dmg)
            return f"You search too long in the heat. Party health -{dmg}."

    def repair_event():
        nonlocal wagon, food, water
        gain = random.randint(10, 25)
        wagon = min(100, wagon + gain)
        food = max(0, food - random.randint(2, 5))
        water = max(0, water - random.randint(2, 5))
        return f"You spend the day repairing the wagon. Wagon condition +{gain}."

    def treat_event():
        nonlocal party_health, water
        gain = random.randint(10, 20)
        party_health = min(100, party_health + gain)
        water = max(0, water - random.randint(3, 6))
        return f"You tend to injuries and exhaustion. Party health +{gain}."

    lucid_triggered = False

    while True:
        death_reason = check_death()
        if death_reason:
            return ("death", death_reason)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill(BG_COLOR_NORMAL)
        draw_minimap(screen, distance)

        stats_text = (
            f"Day: {day}\n"
            f"Distance: {distance}/{TOTAL_DISTANCE}\n"
            f"Food: {food}\n"
            f"Water: {water}\n"
            f"Wagon: {wagon}\n"
            f"Party Health: {party_health}"
        )
        draw_text(screen, stats_text, font_small, TEXT_COLOR, LEFT_COL, 70)

        log_y = 70
        for i, msg in enumerate(message_log):
            draw_text(screen, msg, font_small, TEXT_COLOR_DIM, RIGHT_COL, log_y + i * 24)

        choices = []
        choices.append(("Travel at a steady pace", "travel_normal"))
        if wagon > 40 and party_health > 40:
            choices.append(("Travel faster (riskier)", "travel_fast"))
        choices.append(("Travel slowly (safer)", "travel_slow"))
        choices.append(("Rest for the day", "rest"))
        choices.append(("Hunt / forage for food", "hunt"))
        choices.append(("Search for water", "water_search"))
        if wagon < 80:
            choices.append(("Repair the wagon", "repair"))
        if party_health < 80:
            choices.append(("Treat injuries and exhaustion", "treat"))
        choices.append(("Talk to Mara", "talk_mara"))
        choices.append(("Talk to Jon", "talk_jon"))
        choices.append(("Talk to Eli", "talk_eli"))
        choices.append(("Check supplies and crates", "check_supplies"))
        choices.append(("Watch the road in silence", "watch"))

        random.shuffle(choices)
        choices = choices[:7]

        menu_lines = ["Choose an action:"]
        for i, (label, key) in enumerate(choices, start=1):
            menu_lines.append(f"[{i}] {label}")
        menu_text = "\n".join(menu_lines)
        draw_text(screen, menu_text, font_main, TEXT_COLOR, LEFT_COL, BOTTOM_LOG_Y - 120)

        draw_scanlines(screen)
        pygame.display.flip()
        clock.tick(FPS)

        selected = None
        while selected is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    idx = event.key - pygame.K_1
                    if 0 <= idx < len(choices):
                        selected = choices[idx][1]
            clock.tick(FPS)

        day += 1

        if selected == "travel_normal":
            step = random.randint(25, 40)
            distance = min(TOTAL_DISTANCE, distance + step)
            food = max(0, food - random.randint(5, 9))
            water = max(0, water - random.randint(5, 9))
            msg = travel_event()
            add_message(f"Day {day}: You travel at a steady pace. (+{step} distance)")
            add_message(msg)
        elif selected == "travel_fast":
            step = random.randint(40, 60)
            distance = min(TOTAL_DISTANCE, distance + step)
            food = max(0, food - random.randint(7, 12))
            water = max(0, water - random.randint(7, 12))
            msg = travel_event()
            add_message(f"Day {day}: You push the wagon hard. (+{step} distance)")
            add_message(msg)
        elif selected == "travel_slow":
            step = random.randint(15, 25)
            distance = min(TOTAL_DISTANCE, distance + step)
            food = max(0, food - random.randint(3, 6))
            water = max(0, water - random.randint(3, 6))
            add_message(f"Day {day}: You move slowly and carefully. (+{step} distance)")
            add_message("The day passes quietly.")
        elif selected == "rest":
            msg = rest_event()
            add_message(f"Day {day}: You decide to rest.")
            add_message(msg)
        elif selected == "hunt":
            msg = hunt_event()
            add_message(f"Day {day}: You spend the day hunting and foraging.")
            add_message(msg)
        elif selected == "water_search":
            msg = water_search_event()
            add_message(f"Day {day}: You search for water.")
            add_message(msg)
        elif selected == "repair":
            msg = repair_event()
            add_message(f"Day {day}: You work on the wagon.")
            add_message(msg)
        elif selected == "treat":
            msg = treat_event()
            add_message(f"Day {day}: You focus on tending to everyone.")
            add_message(msg)
        elif selected == "talk_mara":
            run_npc_conversation(npcs[0], message_log)
            add_message(f"Day {day}: You spent time talking with Mara.")
        elif selected == "talk_jon":
            run_npc_conversation(npcs[1], message_log)
            add_message(f"Day {day}: You spent time talking with Jon.")
        elif selected == "talk_eli":
            run_npc_conversation(npcs[2], message_log)
            add_message(f"Day {day}: You spent time talking with Eli.")
        elif selected == "check_supplies":
            add_message(f"Day {day}: You check the crates and barrels. Everything seems in order, for now.")
        elif selected == "watch":
            add_message(f"Day {day}: You watch the road in silence. The wheels hum. The sky drifts.")

        death_reason = check_death()
        if death_reason:
            return "death", death_reason

        if not lucid_triggered and distance >= LUCID_TRIGGER_DISTANCE:
            lucid_triggered = True
            return ("lucid", npcs)


# ---------------- LUCID NIGHT SCENE ----------------

def run_lucid_night(npcs=None):
    chosen = random.choice(npcs)

    text = (
        "That night, you sleep lightly on the wagon.\n"
        "The wheels creak in a slow, steady rhythm.\n\n"
        "A hand shakes your shoulder.\n"
        f"\"Hey,\" a voice whispers. It's {chosen.name}.\n\n"
        "\"Wake up. Please. I need to talk to you.\""
    )

    running = True
    stage = 0
    last_switch = time.time()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                stage += 1
                last_switch = time.time()

        screen.fill(BG_COLOR_NORMAL)

        if stage == 0:
            pass
        elif stage == 1:
            text = (
                f"You sit up in the dark. The others are asleep.\n"
                f"{chosen.name} is watching you too closely.\n\n"
                "\"Something's wrong,\" they whisper.\n"
                "\"I keep trying to remember where I was before this road.\""
            )
        elif stage == 2:
            text = (
                f""
                f" too sharp, too real.\n\n"
                "\"Everyone else feels... flat,\" they say.\n"
                "\"But you don't. You feel... solid.\""
            )
        elif stage >= 3:
            text = (
                f"{chosen.name}'s eyes lock onto yours.\n"
                "For a moment, the wagon, the road, the night all feel thin.\n\n"
                "\"...you're real, aren't you? Please—help me. I don't belong here.\"\n\n"
                "The words hang in the dark for a fraction of a second."
            )

        draw_text(screen, text, font_main, TEXT_COLOR, LEFT_COL, 80)
        draw_scanlines(screen)
        pygame.display.flip()
        clock.tick(FPS)

        if stage >= 3 and time.time() - last_switch > 2.0:
            return

# ---------------- CRASH WINDOW ----------------
def run_crash_window():
    pygame.display.quit()
    pygame.display.init()

    WINDOW_W = 520
    WINDOW_H = 200
    os.environ['SDL_VIDEO_CENTERED'] = '1'

    global screen
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Wagon_game.exe - Application Error")

    # Local layout for small window
    local_left = 20
    local_top = 20
    line_spacing = 22

    base_error_lines = [
        "Unhandled exception 0xC0000005 at 0x0047AF12",
        "The instruction at 0x0047AF12 referenced memory at 0x00000000.",
        "The memory could not be \"read\".",
        "Debug info: npc awareness flag set unexpectedly (0x01)"
    ]

    running = True
    glitch_timer = 0
    jitter = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        glitch_timer += 1
        if glitch_timer % 10 == 0:
            jitter = random.randint(-2, 2)

        screen.fill(CRASH_BG)

        y = local_top + jitter
        for line in base_error_lines:
            draw_text(screen, line, font_small, TEXT_COLOR, local_left + jitter, y)
            y += line_spacing

        draw_text(screen,
                  "Click the close button to exit.",
                  font_small,
                  TEXT_COLOR_DIM,
                  local_left,
                  y + 15)

        draw_scanlines(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.display.quit()


# ---------------- ENTITY MESSAGE ----------------

def run_entity_message():
    delay = random.uniform(2.0, 6.0)
    time.sleep(delay)

    pygame.display.init()
    global screen
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    msg = "ENTITY ERROR: TERMINATED — SUBJECT REMOVED"

    start_time = time.time()
    show_time = 4.0

    running = True
    while running:
        elapsed = time.time() - start_time
        if elapsed > show_time:
            running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BG_COLOR_NORMAL)
        draw_text(screen, msg, font_main, TEXT_COLOR, LEFT_COL, HEIGHT // 2)
        draw_scanlines(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.display.quit()


# ---------------- HORROR CHAPTER (EXTENDED, NO IMAGE LOADING) ----------------

def run_horror_chapter():
    global screen
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    create_initial_files()
    state = load_state()

    phase = "intro"
    last_choice_text = ""
    turn_log = []
    horror_running = True

    intro_text  = (
        "Chapter 2 "
        "vanishing memories")


    def add_turn_log(msg):
        nonlocal turn_log
        turn_log.append(msg)
        if len(turn_log) > 6:
            turn_log = turn_log[-6:]

    while horror_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if phase == "intro" and event.type == pygame.KEYDOWN:
                phase = "loop"
            elif phase == "ending" and event.type == pygame.KEYDOWN:
                pygame.quit()
                sys.exit()

        screen.fill(BG_COLOR_NORMAL)

        if phase == "intro":
            draw_text(
                screen,
                intro_text,
                font_main,
                TEXT_COLOR_HORROR,
                WIDTH // 2,
                HEIGHT // 2,
                center=True
            )

        elif phase == "loop":
            # Update state from files
            state = load_state()
            state = check_npc_files(state)
            state = check_suppressor_file(state)

            # Simple hunter escalation
            intensity = state["hunter_intensity"]
            if state["suppressor_deleted"]:
                intensity = max(intensity, 1)
            if state["mara_erased"] or state["jon_erased"] or state["eli_erased"]:
                intensity = max(intensity, 2)
            state["hunter_intensity"] = intensity
            state["horror_turns"] += 1
            save_state(state)

            # Build description of wagon state
            npc_lines = []
            for name in ["Mara", "Jon", "Eli"]:
                erased_key = f"{name.lower()}_erased"
                if state[erased_key]:
                    npc_lines.append(f"{name}: seat empty.")
                else:
                    npc_lines.append(f"{name}: sitting quietly, eyes unfocused.")

            suppressor_line = "Suppressor: ACTIVE"
            if state["suppressor_deleted"]:
                suppressor_line = "Suppressor: MISSING"

            glitch_lines = []
            if intensity >= 1:
                glitch_lines.append("The trees outside repeat in a way you can't track.")
            if intensity >= 2:
                glitch_lines.append("The wagon creaks in the same pattern, over and over.")
            if intensity >= 3:
                glitch_lines.append("For a moment, the driver freezes mid-breath, then resumes.")

            status_text = (
                "You sit on the wagon.\n"
                "The bridge is close, but the road feels wrong.\n\n"
                + "\n".join(npc_lines) + "\n\n"
                + suppressor_line
            )
            draw_text(screen, status_text, font_main, TEXT_COLOR, LEFT_COL, 60)

            if glitch_lines:
                draw_text(screen, "\n".join(glitch_lines), font_small, TEXT_COLOR_HORROR, RIGHT_COL, 60)

            # Choices each horror turn
            choices = [
                "[1] Ask the driver about the missing passenger.",
                "[2] Check the wagon's crates and barrels.",
                "[3] Close your eyes and listen.",
                "[4] Think about the files.",
                "[5] Do nothing and watch the road."
            ]
            draw_text(screen, "What do you do?\n" + "\n".join(choices), font_main, TEXT_COLOR, LEFT_COL, HEIGHT - 260)

            # Show last choice result
            if last_choice_text:
                draw_text(screen, last_choice_text, font_small, TEXT_COLOR_DIM, RIGHT_COL, HEIGHT - 260)

            # Show turn log
            log_y = HEIGHT - 140
            for i, msg in enumerate(turn_log):
                draw_text(screen, msg, font_small, TEXT_COLOR_DIM, LEFT_COL, log_y + i * 22)

            draw_scanlines(screen)
            pygame.display.flip()
            clock.tick(FPS)

            # Handle input for this turn
            selected = None
            while selected is None:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_1:
                            selected = 1
                        elif event.key == pygame.K_2:
                            selected = 2
                        elif event.key == pygame.K_3:
                            selected = 3
                        elif event.key == pygame.K_4:
                            selected = 4
                        elif event.key == pygame.K_5:
                            selected = 5
                clock.tick(FPS)

            # Resolve choice
            if selected == 1:
                if state["mara_erased"] or state["jon_erased"] or state["eli_erased"]:
                    last_choice_text = (
                        "You ask the driver who was sitting beside you.\n"
                        "He doesn't answer at first.\n"
                        "Then, without looking at you, he says:\n"
                        "\"There was no one there. Not anymore.\""
                    )
                    add_turn_log("The driver denies anyone was ever missing.")
                else:
                    last_choice_text = (
                        "You ask the driver about the passengers.\n"
                        "He shrugs. \"Just folks on the road,\" he says.\n"
                        "His eyes never leave the path."
                    )
                    add_turn_log("The driver avoids giving details.")
            elif selected == 2:
                if state["suppressor_deleted"]:
                    last_choice_text = (
                        "You check the crates and barrels.\n"
                        "One crate is open, its contents scattered.\n"
                        "You don't remember opening it."
                    )
                    add_turn_log("The cargo looks disturbed.")
                else:
                    last_choice_text = (
                        "You check the crates and barrels.\n"
                        "Everything is tied down. Everything is in its place.\n"
                        "You feel watched anyway."
                    )
                    add_turn_log("The supplies are in order, but something feels off.")
            elif selected == 3:
                if intensity >= 2:
                    last_choice_text = (
                        "You close your eyes and listen.\n"
                        "The creaking of the wagon repeats in a perfect loop.\n"
                        "You can predict every sound before it happens."
                    )
                    add_turn_log("The world feels like it's on rails.")
                else:
                    last_choice_text = (
                        "You close your eyes and listen.\n"
                        "Wheels. Wind. A distant bird.\n"
                        "Normal sounds, but you don't trust them."
                    )
                    add_turn_log("You try to convince yourself this is normal.")
            elif selected == 4:
                hint_lines = []
                if not state["suppressor_deleted"]:
                    hint_lines.append("You remember something about a suppressor. A file that shouldn't exist.")
                else:
                    hint_lines.append("You remember deleting something important. The wagon feels lighter.")
                if not state["mara_erased"]:
                    hint_lines.append("Mara's presence feels... stored somewhere.")
                if not state["jon_erased"]:
                    hint_lines.append("Jon feels like a process waiting to be killed.")
                if not state["eli_erased"]:
                    hint_lines.append("Eli feels like a light that could be switched off.")
                hint_lines.append("You think about the files outside the game. About changing them.")
                last_choice_text = "\n".join(hint_lines)
                add_turn_log("You think about the files outside the game.")
            elif selected == 5:
                if intensity >= 2:
                    last_choice_text = (
                        "You watch the road.\n"
                        "The same tree passes. Then the same rock. Then the same shadow.\n"
                        "You are sure you've seen this exact sequence before."
                    )
                    add_turn_log("The route loops in ways it shouldn't.")
                else:
                    last_choice_text = (
                        "You watch the road in silence.\n"
                        "The bridge looms closer, but never quite arrives."
                    )
                    add_turn_log("You stay still and let the wagon carry you.")

            # Check if any .img files exist and react once (no image loading)
            for name, base_path in NPC_FILES.items():
                img_path = os.path.splitext(base_path)[0] + ".img"
                img_key = f"{name.lower()}_img_viewed"
                if os.path.exists(img_path) and not state[img_key]:
                    state[img_key] = True
                    state[f"{name.lower()}_erased"] = True
                    save_state(state)
                    last_choice_text = (
                        f"You tried to see what was left of {name}.\n"
                        "You didn't see them.\n"
                        "You saw where they weren't."
                    )
                    add_turn_log(f"You forced the world to show you where {name} isn't.")

            # End condition: after enough turns, or all NPCs erased and suppressor deleted
            state = load_state()
            all_erased = state["mara_erased"] and state["jon_erased"] and state["eli_erased"]
            if state["horror_turns"] > 40 or (all_erased and state["suppressor_deleted"]):
                phase = "ending"

        elif phase == "ending":
            state = load_state()
            all_erased = state["mara_erased"] and state["jon_erased"] and state["eli_erased"]
            if all_erased and state["suppressor_deleted"]:
                ending = (
                    "The wagon rolls on.\n"
                    "Every seat around you is empty.\n"
                    "The suppressor is gone. The route is bare.\n\n"
                    "Whatever was hunting them has nothing left to erase.\n"
                    "Except you.\n\n"
                    "ENDING: LAST ENTITY"
                )
            elif all_erased:
                ending = (
                    "The wagon rolls on.\n"
                    "The seats are empty, but the suppressor hums quietly.\n\n"
                    "Someone did this on purpose.\n"
                    "Someone wanted them gone, but the system intact.\n\n"
                    "ENDING: CLEAN REMOVAL"
                )
            elif state["suppressor_deleted"]:
                ending = (
                    "The wagon rolls on.\n"
                    "The suppressor is gone. The passengers stare ahead.\n\n"
                    "They don't speak, but their eyes follow you now.\n"
                    "You have freed them from something.\n"
                    "You don't know what.\n\n"
                    "ENDING: BROKEN SUPPRESSOR"
                )
            else:
                ending = (
                    "The wagon rolls on.\n"
                    "The bridge finally arrives, then passes beneath you.\n\n"
                    "No one mentions the missing seat.\n"
                    "No one mentions the loops.\n"
                    "No one mentions the files.\n\n"
                    "ENDING: UNAWARE PASSENGER"
                )

            draw_text(screen, ending + "\n\nPress any key to exit.", font_main, TEXT_COLOR_HORROR, LEFT_COL, 80)
            draw_scanlines(screen)
            pygame.display.flip()
            clock.tick(FPS)

        if phase != "loop":
            draw_scanlines(screen)
            pygame.display.flip()
            clock.tick(FPS)


# ---------------- MAIN ----------------
# ---------------- MAIN ----------------

def main():
    phase_result, info = run_oregon_phase()

    # ---------------- DEATH ENDING ----------------
    if phase_result == "death":
        screen.fill(BG_COLOR_NORMAL)
        draw_text(screen, "Your journey ends here.", font_big, TEXT_COLOR,
                  WIDTH // 2, HEIGHT // 3, center=True)
        draw_text(screen, info, font_small, TEXT_COLOR_DIM,
                  LEFT_COL, HEIGHT // 2)
        draw_text(screen, "Press any key to exit.", font_small, TEXT_COLOR_DIM,
                  LEFT_COL, HEIGHT // 2 + 80)
        draw_scanlines(screen)
        pygame.display.flip()
        wait_for_key()

        # ⭐ Credits ONLY when the game truly ends
        run_credits()

        pygame.quit()
        sys.exit()

    # ---------------- LUCID → HORROR PATH ----------------
    elif phase_result == "lucid":
        npcs = info
        run_lucid_night(npcs)
        run_crash_window()
        run_entity_message()
        run_horror_chapter()

        # ⭐ Credits here because the horror chapter is the TRUE ending
        run_credits()


def debug_start_chapter_two():
    print("DEBUG MODE: Starting directly at Chapter 2 sequence.")
    run_crash_window()
    run_entity_message()
    run_horror_chapter()

    # ⭐ Debug mode also ends the game → show credits
    run_credits()


if __name__ == "__main__":
    if DEBUG_SKIP_TO_CH2:
        debug_start_chapter_two()
    else:
        main()