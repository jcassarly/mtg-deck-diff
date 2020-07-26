#! /usr/bin/awk -f

# This script allows the user to choose from a Magic: The Gathering deck archetype
# from the Legacy format using mtgtop8 and then displays all the cards in the most
# recent 20 decks (if there are that many) along with the number of decks from that
# archetype that play the card and the average frequency.  Furthermore, after selecting
# two decks, the diff between each deck is displayed.
# The mainboard and sideboards are also separated
BEGIN {
    print "Content-type:text/html\n"

    # define some global constants for filepaths
    HOME = "/tmp/deck_home"
    ARCHETYPE_LISTING = "/tmp/deck_listing"
    DECK_BASE = "/tmp/deck"
    SORTED_DECK_LIST = "/tmp/sorted_deck"

    MTGTOP8_URL = "https://www.mtgtop8.com/"
    FORMAT_NAME = "Legacy"
    FORMAT_TAG = "LE"

    init_style()
    print_archetype_form()
    init_script()
    display_chosen_archetype()
}

# Sets some styleline for the display table
function init_style()
{
    print "<head>"
    print "<style>"
    print "table {"
    print "    border-collapse: collapse;"
    print "}"
    print "td, th {"
    print "    padding-left: 5px;"
    print "    padding-right: 5px;"
    print "}"
    print "th {"
    print "    background-color: #444444;"
    print "    color: #ffffff;"
    print "}"
    print "tr:nth-child(odd) {"
    print "    background-color: #dddddd;"
    print "}"
    print "th#h01 {"
    print "    background-color: #ffffff;"
    print "    border: none;"
    print "    color: #000000;"
    print "}"
    print "</style>"
    print "</head>"
}

function init_script()
{
    # https://www.w3schools.com/howto/howto_js_trigger_button_enter.asp was used as a reference
    print "<script>"
    print "var textarea = document.getElementById('deck_text');"
    print "const ENTER_KEY = 13;"
    print ""
    print "textarea.addEventListener('input', function(event) {"
    print "    textarea.rows = Math.max(Math.min(textarea.value.split('\\n').length, 30), 7)"
    print "});"
    print "</script>"
}

# Display's the form for the user to choose an archetype
# downloads the Legacy format page from mtgtop8 to get the archetype list
function print_archetype_form()
{
    print "<form method='GET' action='project2.cgi' align='center' id='input_form'>"
    print "<label for='DECK'>Deck Archetype you want:</label>"
    print "<select name='DECK'>"

    system("wget -O " HOME " \"" MTGTOP8_URL "format?f=" FORMAT_TAG "\"")
    options = ""
    while (getline < HOME)
    {
        options = options option_if_archetype($0)
    }
    print options
    print "</select>"
    print "<input type='submit'>"
    print "</form>"

    print "<div align='center'>"
    print "<label for='DECK_DATA'>Decklist You Own</label><br />"
    printf "<textarea form='input_form' "
    printf           "id='deck_text'"
    printf           "name='DECK_DATA' "
    printf           "rows='7' "
    printf           "cols='50' "
    printf           "placeholder='Enter your Decklist in the following format (MTGO format):\n"
    printf                        "3 Force of Will\n"
    printf                        "4 Brainstorm\n"
    printf                        "1 True-Name Nemesis\n"
    printf                        "Sideboard\n"
    printf                        "2 Tormod\'s Crypt\n"
    printf                        "1 Blue Elemental Blast'>"
    printf "</textarea>\n"
    print "</div>"


    close(HOME)
}


# TODO: update
# Prints an html option tag with the archetype link as the value and the
# archetype name as the text assuming line contains an archetype definition
# @param line a line in the format: <td class=S12><a  href=archetype?a=213&meta=39&f=LE>UR Delver</a></td>
function option_if_archetype(line)
{
    # all the lines with "archetype" look like the following:
    # <td class=S12><a  href=archetype?a=213&meta=39&f=LE>UR Delver</a></td>
    if (line ~ "archetype")
    {
        # extract the link and deck and print them to an option tag
        # /<td class=S12><a  href=(link)>(deck)<\/a><\/td>/
        link_start = line; sub(".*<a.*href=","",link_start);
        link = link_start; sub(">.*","",link)
        deck = link_start; sub("[^>]+>","", deck); sub("<.*","", deck)
        return "<option value=\"" link "\">" deck "</option>\n"
    }
    else
    {
        return ""
    }
}

# Displays the data table for the chosen archetype from the query string
function display_chosen_archetype()
{
    split(ENVIRON["QUERY_STRING"],query_data,/&/)
    for (indiv_data in query_data) { split(query_data[indiv_data],data,/=/); val[data[1]] = data[2] }

    if (val["DECK"] == "")
    {
        print "<p>No Deck Selected</p>"
    }
    else
    {
        system("echo \"" decoded_deck(val["DECK_DATA"]) "\" > " DECK_BASE 1)
        deck_data(user_main, user_main_quantities, user_side, user_side_quantities, 1)

        deck_url = decoded_url(val["DECK"])
        deck_count = download_decks(deck_url)
        deck_data(target_main, target_main_quantities, target_side, target_side_quantities, deck_count)

        diff_quantities(user_main_quantities, target_main_quantities, main_diff)
        diff_quantities(user_side_quantities, target_side_quantities, side_diff)

        # print out the table
        print "<table>"
        print "<tr>"
        print "<th colspan='2' id='h01'><h1>" end_archetype "</h1></th>"
        print "</tr>"
        print "<tr>"

        write_to_table(user_main, user_main_quantities, target_main, target_main_quantities, main_diff, deck_count, "Main")

        write_to_table(user_side, user_side_quantities, target_side, target_side_quantities, side_diff, deck_count, "Side")

        print "</tr>"
        print "</table>"
    }
}

function diff_quantities(user_quantities, target_quantities, diff)
{
    for (cardname in target_quantities)
    {
        diff[cardname] = target_quantities[cardname] - user_quantities[cardname]
    }

    for (cardname in user_quantities)
    {
        # need to make sure cards that are not in the end values still appear in the diff
        if (diff[cardname] == "" || diff[cardname] <= 0)
        {
            diff[cardname] = "-"
        }
    }
}

# Decodes url encoded ? = and & characters
# @param url_to_decode a string with url encoded values to decrypt
# @return the decoded url
function decoded_url(url_to_decode)
{
    url = url_to_decode
    gsub("%3F", "?", url)
    gsub("%3D", "=", url)
    gsub("%26", "\\&", url)
    return url
}

function decoded_deck(deck_list_to_decode)
{
    deck_list = deck_list_to_decode
    gsub("\+", " ", deck_list)
    gsub("%0D", "\r", deck_list)
    gsub("%0A", "\n", deck_list)
    gsub("%2C", ",", deck_list)
    gsub("%27", "'", deck_list)
    gsub("%2F", "/", deck_list)
    gsub("%2D", "-", deck_list)
    gsub("(%C6)|%C3%86", "&#x00E6;", deck_list)
    return deck_list
}

# Downloads the top 20 (or less if there are not 20) decks for the archetype at the given url
# @param url a part of the mtgtop8 url in the format: archetype?a=213&meta=39&f=LE
# @return the number of decks downloaded
function download_decks(url)
{
    system("wget -O " ARCHETYPE_LISTING " \"" MTGTOP8_URL url "\"")

    # need to generate link with the following pattern: mtgo?d=373257&f=Legacy_UR_Delver_by_silviawataru
    #                                                         |deckno|        |deck name|  |player name |
    # specifically need to find the "d=" number and "f=" value
    next_url = ""
    deck_count = 0
    while (getline < ARCHETYPE_LISTING)
    {
        # The following if statements extract different values from the deck listing
        # the order they are in is also their relative order in the file such that
        # a later if statement will never evaluate true more than a previous if statement

        # Extracts the name of the archetype for use when printing the decks
        #<tr><td colspan=7><div class=w_title align=center>UR Delver decks</div></td></tr>
        #                                                 |   archetype   |
        if (match($0, "w_title.* decks"))
        {
            archetype = html_element_content($0)
        }

        # extracts the deck number and specific name for this list
        # <td><a href=event?e=24758&d=373257&f=LE>UR Delver</a></td>
        #                            |deckno|    |deck name|
        if (match($0, "event\\?e=.*d="))
        {
            # extract the deck number ("d=#")
            deck_num = value_between(".*d=", "&.*", $0);
            next_url = "mtgo?d=" next_url deck_num

            # extract the deck name out of this line too
            deck_name = value_between(".*" FORMAT_TAG ">", "<.*", $0); spaces_to_underscores(deck_name)
            next_url = next_url "&f=" FORMAT_NAME "_" deck_name
        }

        # since the above statement for the deck name and number from the line above the playername line
        # this if statement finds, we can extract the player name here and then download the
        # decklist
        # <td><a class=player href=search?player=silviawataru>silviawataru</a></td>
        #                                                    |player name |
        if (match($0, "class=player"))
        {
            # extract the player name
            name = html_element_content($0); spaces_to_underscores(name)
            next_url = next_url "_by_" name

            # download the decklist
            deck_count = deck_count + 1
            system("wget -O " DECK_BASE deck_count " \"" MTGTOP8_URL next_url "\"")
            system("sleep 0.5")

            next_url = ""
        }
    }

    close(ARCHETYPE_LISTING)

    return deck_count
}

# Extracts the HTML element content from the line (removes leading whitespace and removes
# HTML tags)
# @param line a string to sanitize into just the HTML element content
# @return the html element content
function html_element_content(line)
{
    content = line; sub("^[\t ]+", "", content); gsub("<[^>]+>", "", content);
    return content
}

# Extracts the value between the two given regex patters
# @param begin_pattern a regex pattern for the beginning of the line to get to
#                      the start of the desired value
# @param end_pattern   a regex pattern that goes from the end of the desired value
#                      to the end of the line
# @param line          the line to extract a value from
# @return the value between the patterns
function value_between(begin_pattern, end_pattern, line)
{
    value = line; sub(begin_pattern, "", value); sub(end_pattern, "", value)
    return value
}

# Converts all spaces to underscores in str
function spaces_to_underscores(str)
{
    gsub(" ", "_", str)
}

# Reads each deck and dumps the appearance and quantity data into the given parameters
# the given array parameters will be written to and index by card named in the deck data
# @param main_board an array to write the number of appearances of mainboard cards to
# @param main_board_quantities an array to write the total quantity of each mainboard card to
# @param side_board an array to write the number of appearances of sideboard cards to
# @param side_board_quantities an array to write the total quantity of each sideboard card to
# @param deck_count the number of decks to parse data from
function deck_data(main_board, main_board_quantities, side_board, side_board_quantities, deck_count)
{
    # need to parse the deck lists into two arrays of [cardname] = num_decks_with_card
    # 1 for mainboard and 1 for sideboard
    for (i = 1; i <= deck_count; i++)
    {
        is_mainboard = 1
        current_deck = (DECK_BASE i)
        while (getline < current_deck)
        {
            if ($0 !~ "Sideboard")
            {
                quantity = $0; sub(" .*", "", quantity)
                cardname = $0; sub("[^ ]+ ", "", cardname); cardname = tolower(cardname)
                if (!match(quantity, "[0-9]+"))
                {
                    # do nothing and ignore the line
                }
                else if (is_mainboard)
                {
                    main_board[cardname]++
                    main_board_quantities[cardname] = main_board_quantities[cardname] + quantity
                }
                else
                {
                    side_board[cardname]++
                    side_board_quantities[cardname] = side_board_quantities[cardname] + quantity
                }
            }
            else
            {
                is_mainboard = 0
            }
        }

        close(current_deck)
    }

    for (cardname in main_board)
    {
        main_board_quantities[cardname] = main_board_quantities[cardname] / main_board[cardname]

        # if a card appears in less than 20% of decklists it doesnt exist and is likely a mislabelled deck
        if (main_board[cardname] < (0.2 * deck_count))
        {
            delete main_board[cardname]
            delete main_board_quantities[cardname]
        }
    }

    for (cardname in side_board)
    {
        side_board_quantities[cardname] = side_board_quantities[cardname] / side_board[cardname]
    }
}

# Sort the given arrays of appearances in the given board and the quantities of each
# of those cards into SORTED_DECK_LIST
# @param board an array indexed by cardname representing the main/sideboard with appearances of each card
# @param quantities an array indexed by cardnames with quantities for each card in the board
function sort_to_file(diff)
{
    arr_string = ""
    for (element in diff)
    {
        arr_string = arr_string element "\n"
    }

    system("echo \"" arr_string "\" | sort -nr > " SORTED_DECK_LIST)
}

# Writes the given board and quantities to the board_name table in html
# @param board an array indexed by cardname representing the main/sideboard with appearances of each card
# @param quantities an array indexed by cardnames with quantities for each card in the board
# @param board_name a string that is the name of the table to write to
function write_to_table(user_board, user_quantities, target_board, target_quantities, diff, deck_count, board_name)
{
    print "<td valign='top' style='border: none;'>"
    print "<table>"
    print "<tr>"
    print "<th>" board_name "board Cardname</th>"
    print "<th>Owned Quantity</th>"
    print "<th>Average Quantity in Top " deck_count " " archetype "</th>"
    print "<th>Number of " archetype " Containing</th>"
    print "<th>Suggested Amount Needed</th>"
    print "</tr>"

    row_num = 0
    sort_to_file(diff)
    while (getline < SORTED_DECK_LIST)
    {
        if ($0 != "")
        {
            cardname = $0
            user_frequency = user_board[cardname] + 0
            target_frequency = target_board[cardname] + 0

            even_row = (row_num % 2) == 0
            card_owned = user_frequency > 0
            if (even_row && card_owned)
            {
                print "<tr style='background-color: #eeffee;'>"
            }
            else if (!even_row && card_owned)
            {
                print "<tr style='background-color: #ddeedd;'>"
            }
            else if (even_row && !card_owned)
            {
                print "<tr style='background-color: #ffeeee;'>"
            }
            else
            {
                print "<tr style='background-color: #eedddd;'>"
            }
            print "<td>" capitalize_each_word(cardname) "</td>"

            if (user_frequency > 0)
            {
                print "<td align='center'>" user_quantities[cardname] "</td>"
            }
            else
            {
                print "<td align='center'>0</td>"
            }

            if (target_frequency > 0)
            {
                printf "<td align='center'>%.2f</td>", target_quantities[cardname]
                print "<td align='center'>" target_frequency " / " deck_count "</td>"
            }
            else
            {
                print "<td align='center'>-</td>"
                print "<td align='center'>-</td>"
            }

            if (diff[cardname] == "-")
            {
                # light green background to indicate no more of the card is needed
                print "<td align='center' style='background: #66f859;'>&#10004;</td>"
            }
            else
            {
                # light red backgrounf to indicate the card is not in the start deck
                print "<td align='center' style='background: #ff3838;'>" round_up(diff[cardname]) "</td>"
            }

            print "</tr>"
            row_num++
        }
    }

    print "</table>"
    print "</td>"

    close(SORTED_DECK_LIST)
}

function round_up(value)
{
    rounded_down = int(value)
    if (value == rounded_down)
    {
        return value
    }
    else
    {
        return rounded_down + 1
    }
}

function capitalize_each_word(line)
{
    return capitalize_each_word_with_separator(capitalize_each_word_with_separator(line, " "), "-")
}

function capitalize_each_word_with_separator(line, separator)
{
    split(line, words, separator)
    out_line = ""
    for (i in words)
    {
        out_line = out_line toupper(substr(words[i], 1, 1)) substr(words[i], 2) separator
    }

    sub(separator "$", "", out_line)

    return out_line
}
