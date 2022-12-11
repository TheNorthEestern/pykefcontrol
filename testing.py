# script_version=1
import pykefcontrol as pkf
import sys
import socket
from rich import print
from rich.console import Console
import ipaddress
import time
import requests

console = Console()

DEBUG = True
ALL_TESTS_OUTPUTS = {}


def newline():
    print("\n")


def get_local_ip():
    return (
        (
            [
                ip
                for ip in socket.gethostbyname_ex(socket.gethostname())[2]
                if not ip.startswith("127.")
            ]
            or [
                [
                    (s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close())
                    for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]
                ][0][1]
            ]
        )
        + ["no IP found"]
    )[0]


def check_turn_on(spkr, console):
    counter = 0
    with console.status("Turning on speaker [italic](15s max)[/italic]..."):
        spkr.power_on()
        counter = 0
        while spkr.status == "standby" or counter < 15:
            time.sleep(1)
            counter += 1
    if spkr.status in ["powerOn", "wifi"]:
        console.print(
            f"[bold green]Speaker turned on successfully.[/bold green]",
        )
    elif counter >= 15:
        console.print(
            f"[bold orange_red1]Speaker did not turn on: timeout![/bold orange_red1]",
            f"\n[bold orange_red1]after timeout, status is: {spkr.status}[/bold orange_red1]",
        )
    else:
        console.print(
            f"[bold orange_red1]Unknown speaker status: {spkr.status}[/bold orange_red1]",
        )


def check_turn_off(spkr, console):
    counter = 0
    with console.status("Turning off speaker [italic](15s max)[/italic]..."):
        spkr.shutdown()
        counter = 0
        while spkr.status != "standby" or counter < 15:
            time.sleep(1)
            counter += 1
    if spkr.status == "standby":
        console.print(
            f"[bold green]Speaker turned off successfully.[/bold green]",
        )
    elif counter >= 15:
        console.print(
            f"[bold orange_red1]Speaker did not turn off: timeout![/bold orange_red1]",
            f"\n[bold orange_red1]after timeout, status is: {spkr.status}[/bold orange_red1]",
        )
    else:
        console.print(
            f"[bold orange_red1]Unknown speaker status: {spkr.status}[/bold orange_red1]",
        )


def check_source(spkr, console, source):
    counter = 0
    with console.status(f"Setting source to {source} [italic](15s max)[/italic]..."):
        spkr.source = source
        counter = 0
        while spkr.source != source or counter < 15:
            time.sleep(1)
            counter += 1
    if spkr.source == source:
        console.print(
            f"[bold green]Speaker source set to {source} successfully.[/bold green]",
        )
    elif counter >= 15:
        console.print(
            f"[bold orange_red1]Speaker did not set source to {source}: timeout![/bold orange_red1]",
            f"\n[bold orange_red1]after timeout, source is: {spkr.source}[/bold orange_red1]",
        )
        return -1
    else:
        console.print(
            f"[bold orange_red1]Unknown speaker source: {spkr.source}[/bold orange_red1]",
        )
        return -1


def validate_ip_address(ip_string):
    try:
        ip_object = ipaddress.ip_address(ip_string)
        return str(ip_object)
    except ValueError:
        print(
            f"The IP address '{ip_string}' is not valid.\n\
        Please enter a valid IP address in the form www.xxx.yyy.zzz"
        )
        return -1


def user_confirmation(console, action, msg=None):
    if DEBUG:
        return {action: True}
    else:
        if msg is None:
            console.print("\tDo you confirm the change was successful? (y/n) ", end="")
        else:
            console.print(f"\t{msg} (y/n) ", end="")
        user_input = input()
        while user_input.lower() not in ["y", "n"]:
            console.print("\tPlease enter y (for yes) or n (for no): ", end="")
            user_input = input()
        if user_input.lower() == "y":
            console.print(
                "\t[bold green]✅ Change sucessful for the user ![/bold green]"
            )
            return {action: True}

        else:
            console.print(
                "\t[bold orange_red1]❌ Unsucessful change for the user ![/bold orange_red1]"
            )
            return {action: False}


newline()
console.print("[green3]Testing Utility[/green3]".center(80, "="))


# ====== Check testing utility version ======
try:
    with console.status("Checking if this script is up to date..."):
        with requests.get(
            "https://raw.githubusercontent.com/N0ciple/pykefcontrol/main/testing.py"
        ) as response:
            output = response.text
    version = output.split("# script_version=")[1].split("\n")[0]
    if version == "1":
        console.print(
            f"[bold green]This script is up to date.[/bold green]",
        )
    else:
        console.print(
            "[bold orange_red1]Testing utility is not up to date.[/bold orange_red1]\n\
                Please upgrade with [bold red]`git pull`[/bold red] in the pykefcontrol folder."
        )
except Exception as e:
    console.print("Error:", e, style="red")
    console.print(
        "[bold orange_red1]Could not check testing utility version.[/bold orange_red1]"
    )
    console.print("Continuing anyway... but script version might not be the latest!")

input("Press enter to continue...")


# ====== System info ======

python_version = sys.version
pkf_version = pkf.__version__
computer_ip = get_local_ip()

newline()
print("[cyan3]System info[/cyan3]".center(80, "-"))
print("Python version:", python_version)
if pkf_version == "0.5.1":
    end_msg = "(✅ Latest version)"
else:
    end_msg = "(⚠️ not the latest version, please upgrade with `pip install pykefcontrol --upgrade`)"
print("Pykefcontrol version:", pkf_version, end_msg)
print("Computer local IP:", computer_ip)

# ====== Speaker info ======

newline()

print("[cyan3]KEF Speaker IP Address[/cyan3]".center(80, "-"))
print(
    "Please enter the IP address of your KEF speaker in the form www.xxx.yyy.zzz\n(192.168.0.12 for example)"
)

spkr_ip = validate_ip_address(input("IP Address: "))
while spkr_ip == -1:
    spkr_ip = validate_ip_address(input("IP Address: "))

print("Using speaker IP:", spkr_ip)
newline()
print("[cyan3]Speaker Info[/cyan3]".center(80, "-"))
spkr = pkf.KefConnector(spkr_ip)
with console.status(
    "Getting speaker info...",
):
    try:
        spkr_name = spkr.speaker_name
    except AttributeError:
        print("Error getting speaker Name. Please check your IP address and try again.")
        sys.exit()
    except:
        print("Error. Please check your IP address and try again.")
        sys.exit()
    time.sleep(0.5)
    spkr_mac_address = spkr.mac_address

print("Speaker Infos:")
print("\tIP:", spkr_ip)
print(f'\tName: "{spkr_name}"')
print("\tMAC Address:", spkr_mac_address)
newline()
out = user_confirmation(
    console, "speaker info", msg="Are the speaker information correct?"
)
ALL_TESTS_OUTPUTS.update(out)

# ====== Power & Source Control ======
newline()
print("[cyan3]Power & Source Control[/cyan3]".center(80, "-"))
print(
    "This section will test if your speaker can be [bold]powered on and off[/bold] by pykefcontrol,\nand if it can [bold]switch between sources.[/bold]"
)
input("Press press Enter to continue...")

with console.status("Getting speaker status..."):
    time.sleep(0.5)
    status = spkr.status
newline()
console.print(f"Current speaker status: [dodger_blue1]{status}[/dodger_blue1]")
newline()
if status == "standby":
    console.print(
        "The speaker is currently off. The test sequence will be [blue]->on ->off[/blue] and then a normal turn on"
    )
    input("Press press Enter to continue...")
    check_turn_on(spkr, console)
    out = user_confirmation(console, action="turn on")
    ALL_TESTS_OUTPUTS.update(out)
    check_turn_off(spkr, console)
    out = user_confirmation(console, action="turn off")
    ALL_TESTS_OUTPUTS.update(out)
    spkr.power_on()
elif status in ["powerOn", "wifi", "optical", "aux", "bluetooth"]:
    console.print(
        "The speaker is currently on. The test sequence will be [blue]->off ->on[/blue]"
    )
    input("Press press Enter to continue...")
    check_turn_off(spkr, console)
    out = user_confirmation(console, action="turn off")
    ALL_TESTS_OUTPUTS.update(out)
    check_turn_on(spkr, console)
    user_confirmation(console, action="turn on")
    ALL_TESTS_OUTPUTS.update(out)

# ====== Source Control ======

newline()
console.print("The script will now check that pykefcontrol can switch between sources.")
console.print(
    "It will switch between [bold]wifi, bluetooth, tv, optical, coaxial and analog[/bold]."
)
console.print(
    "[red]Please grab your phone with the application [bold]KEF Connect[/bold] to check that the changes where successful.[/red]"
)
input("Press press Enter to continue...")

issue_with = []
for source in ["wifi", "bluetooth", "tv", "optical", "coaxial", "analog"]:
    out = check_source(spkr, console, source)
    if out == -1:
        issue_with.append(source)
    else:
        out = user_confirmation(console, action="switch to " + source)

        ALL_TESTS_OUTPUTS.update(out)

newline()
console.print(
    "Sources tested: [bold]wifi, bluetooth, tv, optical, coaxial and analog[/bold]"
)
if len(issue_with) == 0:
    console.print(
        "[bold green]All sources were switched successfully.[/bold green]",
    )
else:
    console.print(
        f"[bold orange_red1]The following sources could not be switched to: {issue_with}[/bold orange_red1]",
    )

# ====== Volume Control ======
console.print("[cyan3]Volume Control[/cyan3]".center(80, "-"))
console.print("The script will now check that pykefcontrol can control the volume.")
console.print(
    "[red]Please grab your phone with the application [bold]KEF Connect[/bold] to check that the changes where successful.[/red]"
)
input("Press press Enter to continue...")

newline()
console.print("Getting current volume.")
try:
    vol = spkr.volume
    console.print(f"Current volume: [dodger_blue1]{vol}[/dodger_blue1]")
except Exception as e:
    console.print(f"[bold orange_red1]Error getting volume: {e}[/bold orange_red1]")
    sys.exit()

with console.status("Testing changing volume..."):
    if vol < 10:
        spkr.volume = vol + 5
    else:
        spkr.volume = vol - 5
if vol < 10:
    console.print(
        f"Volume should have been increased by 5.\nCurrent volume: [dodger_blue1]{spkr.volume}[/dodger_blue1]"
    )
    out = user_confirmation(console, action="increase volume")
    ALL_TESTS_OUTPUTS.update(out)
else:
    console.print(
        f"Volume should have been decreased by 5.\nCurrent volume: [dodger_blue1]{spkr.volume}[/dodger_blue1]"
    )
    out = user_confirmation(console, action="decrease volume")
    ALL_TESTS_OUTPUTS.update(out)

current_vol = spkr.volume

# ====== Mute Control ======
console.print("[cyan3]Mute Control[/cyan3]".center(80, "-"))
console.print(
    "The script will now check that pykefcontrol can mute  and unmute the speaker."
)
with console.status("Muting speaker..."):
    spkr.mute()
console.print("Speaker should be muted now.")
out = user_confirmation(console, action="mute speaker")
ALL_TESTS_OUTPUTS.update(out)
with console.status("Unmuting speaker..."):
    spkr.unmute()
console.print(f"Speaker should be unmuted now.\nVolume should be {current_vol}.")
out = user_confirmation(console, action="unmute speaker")
ALL_TESTS_OUTPUTS.update(out)
newline()

# ====== Playback Control ======
console.print("[cyan3]Playback Control[/cyan3]".center(80, "-"))
console.print("The script will now check that pykefcontrol can control playback.")
console.print(
    "[red]Please grab your phone and play music over wifi with [bold]Chromecast, Airplay, Spotify Connect or DLNA[/bold][/red]"
)
newline()
input("Press press Enter to continue...")
console.print(
    "The script will now try to [detect the current song.\n[bold]Make sure that a song is playing.[/bold]"
)
input("Press press Enter to continue...")
with console.status("Detecting song..."):
    song_info = spkr.get_song_information()

console.print(f"Current song informations: [dodger_blue1]{song_info}[/dodger_blue1]")
out = user_confirmation(
    console,
    action="song information",
    msg="Are the informations [bold red] roughly [/bold red] correct?",
)
ALL_TESTS_OUTPUTS.update(out)

console.print("The script will now try to [bold]pause/pause[/bold] the playback.")
console.print("[bold orange1]Make sure that the track is not paused.[/bold orange1]")

input("Press press Enter to continue...")

with console.status("Detecting status..."):
    status = spkr.is_playing
if status:
    console.print(f"The song is detected as [dodger_blue1]playing[/dodger_blue1]")
console.print("The script will now try to [bold]pause[/bold] the playback.")
input("Press press Enter to continue...")
with console.status("Pausing playback..."):
    spkr.toggle_play_pause()
console.print("Playback should be paused now.")
out = user_confirmation(console, action="pause playback")
ALL_TESTS_OUTPUTS.update(out)
newline()
console.print("The script will now try to [bold]resume[/bold] the playback.")
with console.status("Resuming playback..."):
    spkr.toggle_play_pause()
console.print("Playback should be resumed now.")
out = user_confirmation(console, action="resume playback")
ALL_TESTS_OUTPUTS.update(out)
newline()

console.print("The script will now try to [bold]skip to next track[/bold].")
with console.status("Skipping to next track..."):
    spkr.next_track()
console.print("The speaker should be playing the next track now.")
out = user_confirmation(console, action="skip to next track")
ALL_TESTS_OUTPUTS.update(out)
newline()
console.print("The script will now try to [bold]skip to previous track[/bold].")
with console.status("Skipping to previous track..."):
    spkr.previous_track()
console.print("The speaker should be playing the previous track now.")
out = user_confirmation(console, action="skip to previous track")
ALL_TESTS_OUTPUTS.update(out)
newline()

console.print("[cyan3]Sum Up[/cyan3]".center(80, "-"))
console.print("[bold]Working features:[/bold]")
for feature in ALL_TESTS_OUTPUTS:
    if ALL_TESTS_OUTPUTS[feature]:
        console.print(f"\t[green]✓[/green] {feature}")
console.print("[bold]Non working features:[/bold]")
for feature in ALL_TESTS_OUTPUTS:
    if not ALL_TESTS_OUTPUTS[feature]:
        console.print(f"\t[red]✗[/red] {feature}")

console.print("[cyan_blue1]Testing Ended[/cyan_blue1]".center(80, "-"))
console.print("[bold green]Thank you for helping testing Pykefcontrol 🤗[/bold green]")
console.print(
    "[bold orange1]wether all the tests were successful or not, please repport your results on GitHub[/bold orange1]"
)

print("==".center(80, "="))
newline()
