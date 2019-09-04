import csv


def gen_group_list(filename):
    with open(filename, 'rt') as f:
        reader = csv.reader(f)
        my_list = list(reader)

    return my_list

def create_prompt(prompt,group_desc,loc_desc):
    group_desc_pattern = '[GROUPDESC]'
    location_desc_pattern = '[LOCATIONDESC]'
    new_prompt = prompt.replace(group_desc_pattern,group_desc).replace(location_desc_pattern,loc_desc)
    return new_prompt.replace('  ',' ')

def get_prompt_list(filename,prompt):
    my_list = gen_group_list(filename)
    prompt_list = []
    for row in my_list:
        #group_name = row[0]
        group_name, group_desc, loc_desc = row[0], row[1],row[2]
        prompt_list.append([group_name,create_prompt(prompt,group_desc,loc_desc)])

    return prompt_list


#prompt = 'Hey [GROUPDESC]! Come on down to Freewheel Brewing [LOCATIONDESC] for a free stand-up comedy show featuring some of the best comedians in the Bay! Hosts Ryan Goodcase and Ryan Sudhakaran (me) will be serving a comedy flight for all tastes, whether it be dry, wit, or incredibly bitter. So grab a brew, sit back, and enjoy some Good Suds!'
#print(list_of_prompts('goodsuds.csv',prompt))
