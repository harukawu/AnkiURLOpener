# AnkiURLOpener Configuration

This add-on helps you automatically open URLs when studying Anki cards and the answer is revealed.

## Configuration Options

### Profiles
You can create multiple profiles to use with different decks. Each profile can be configured with:

- **field_name**: The name of the field from your Anki card that will be used to replace placeholders in the URL.
- **url_template**: A URL template with a placeholder ({{field_content}}) that will be replaced with content from the specified field.
- **application**: The application to use when opening the URL (leave blank to use the default browser).
- **decks**: A list of deck names that this profile should be used for. The add-on will automatically use the correct profile based on which deck the card belongs to.
- **enabled**: Whether this profile is enabled or not.

## How to Use

1. Create a profile or edit an existing one
2. Enter the name of the field containing the text you want to use in the URL
3. Enter a URL template with {{field_content}} where you want the field text to appear (e.g., `https://www.google.com/search?q={{field_content}}`)
4. Select which application should open the URL (optional - leave blank for default browser)
5. Add the decks that should use this profile by clicking "Add Deck"
6. Make sure the profile is enabled
7. Save the profile

When you review cards from the specified decks, the add-on will automatically use the corresponding profile to open URLs.

**Note:** If a card's deck is not configured in any profile, the add-on will use the default profile. 