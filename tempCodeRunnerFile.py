def get_response(intents_list, intents_json):
    if not intents_list:
        return "I'm sorry, I didn't quite catch that. Can you please provide more details or ask another question?"

    responses = {}
    for intent in intents_json['intents']:
        tags = intent['tag'].split(',')
        for tag in tags:
            responses[tag.strip()] = intent.get('responses', [])

    result = []
    unique_tags = set()  # To store unique tags encountered
    for intent_data in intents_list:
        tags = [tag.strip() for tag in intent_data['intent'].strip().split(',')]
        for tag in tags:
            if tag in responses and tag not in unique_tags:
                unique_tags.add(tag)
                tag_responses = responses[tag]
                if tag_responses:
                    # Select a random response for the tag
                    random_response = random.choice(tag_responses)
                    result.append(random_response)
                else:
                    result.append(f"No responses available for tag {tag}")

    # Join results with two new line gaps between them
    result_with_gaps = '\n\n'.join(result)

    # Add an additional new line gap at the end
    if result_with_gaps:
        result_with_gaps += '\n\n'

    return result_with_gaps if result_with_gaps else "No responses found for provided tags."