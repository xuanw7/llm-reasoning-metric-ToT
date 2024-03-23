import itertools
import numpy as np
from functools import partial
from tot.models import gpt


##############
# Helper function to convet string like "6*9-10" into ["6*9=54.0", "54.0-10=44.0"]
def separate_and_solve(expression):
    import re

    # Helper function to calculate expression result
    def calculate_expression(expr):
        try:
            return round(eval(expr), 3)
        except Exception as e:
            return None

    # Function to extract and solve sub-expressions
    def extract_and_solve(expr):
        steps = []

        pattern = r'(\d+\.?\d*|\([^\(\)]+\))([+\-*\/])(\d+\.?\d*|\([^\(\)]+\))'
        count = 0
        while re.search(pattern, expr):
            for sub_expr in re.finditer(pattern, expr):
                left, operator, right = sub_expr.groups()
                # Solve the current sub-expression
                result = calculate_expression(sub_expr.group())
                if result is not None:
                    steps.append(f"{sub_expr.group()}={result}")
                    # Replace the current sub-expression with its result in the original expression
                    expr = expr.replace(sub_expr.group(), str(result), 1)
                    break
            if (count > 3):
                break
            count += 1
        return steps

    expression = re.sub(r'=', '', expression)

    steps = extract_and_solve(expression)
    return steps



def get_current_numbers(y: str) -> str:
    last_line = y.strip().split('\n')[-1]
    return last_line.split('left: ')[-1].split(')')[0]
##############

def get_value(task, x, y, n_evaluate_sample, cache_value=True, step = 0, expressions = {}):
    value_prompt = task.value_prompt_wrap(x, y)
    current_numbers = get_current_numbers(y)
    if cache_value and value_prompt in task.value_cache:
        return task.value_cache[value_prompt]
    value_outputs = gpt(value_prompt, n=n_evaluate_sample, stop=None)
    
    ##############
    if (step == 2): 
        separated_expression = expressions[current_numbers]
        # print("Current_numbers:" ,current_numbers)
        if (len(separated_expression) == 3 and len(current_numbers.split(" ")) == 3-step):
            # print("Useful Steps:" , tuple(separated_expression))
            task.deadend_set_useful.add(tuple(separated_expression))
        else:
            task.deadend_set_useless.add(tuple(separated_expression))
            # print("Uselss Steps:" , tuple(separated_expression))

    elif (step < 2 and value_outputs and len(value_outputs) != 0):
        value_output = value_outputs[0]
        value_output_lines = value_output.split('\n')
        # print("Current_numbers:" ,current_numbers)
        
        for line in value_output_lines:
            if "=" in line:
                task.efficiency_count += 1
                #(12 - 7) * 8 = 5 * 8 = 40

                line = line.replace(" ", "")
                line = line.replace("(", "")
                line = line.replace(")", "")
                first_expression = line.split("=")[0]

                separated_expression_value = separate_and_solve(first_expression)
                separated_expression_proposal = []
                if (current_numbers in expressions):
                    separated_expression_proposal = expressions[current_numbers]
                else:
                    print("Error: key not found in expressions")
                separated_expression = separated_expression_proposal + separated_expression_value

                if (len(separated_expression) == 3 and len(current_numbers.split(" ")) == 3-step):
                    # print("Useful Steps:" , tuple(separated_expression))
                    task.deadend_set_useful.add(tuple(separated_expression))
                else:
                    task.deadend_set_useless.add(tuple(separated_expression))
                    # print("Uselss Steps:" , tuple(separated_expression))
                
        value_names = value_output_lines[-1]
        
        if ("sure" in value_names.lower()):
            task.efficiency_count -= 1
    #############
    # print("All", separated_expression)

            
    value = task.value_outputs_unwrap(x, y, value_outputs)
    if cache_value:
        task.value_cache[value_prompt] = value
    return value

def get_values(task, x, ys, n_evaluate_sample, cache_value=True, step = 0, expressions = {}):
    values = []
    local_value_cache = {}
    for y in ys:  # each partial output
        if y in local_value_cache:  # avoid duplicate candidates
            value = 0
        else:    
            value = get_value(task, x, y, n_evaluate_sample, cache_value=cache_value, step=step, expressions=expressions)
            local_value_cache[y] = value
        values.append(value)
    return values

def get_votes(task, x, ys, n_evaluate_sample):
    vote_prompt = task.vote_prompt_wrap(x, ys)
    vote_outputs = gpt(vote_prompt, n=n_evaluate_sample, stop=None)
    values = task.vote_outputs_unwrap(vote_outputs, len(ys))
    return values

def get_proposals(task, x, y): 
    propose_prompt = task.propose_prompt_wrap(x, y)
    proposals = gpt(propose_prompt, n=1, stop=None)[0].split('\n')
    return [y + _ + '\n' for _ in proposals]

def get_samples(task, x, y, n_generate_sample, prompt_sample, stop):
    if prompt_sample == 'standard':
        prompt = task.standard_prompt_wrap(x, y)
    elif prompt_sample == 'cot':
        prompt = task.cot_prompt_wrap(x, y)
    else:
        raise ValueError(f'prompt_sample {prompt_sample} not recognized')
    samples = gpt(prompt, n=n_generate_sample, stop=stop)
    return [y + _ for _ in samples]

def solve(args, task, idx, to_print=True):
    global gpt
    gpt = partial(gpt, model=args.backend, temperature=args.temperature)
    print(gpt)
    x = task.get_input(idx)  # input
    ys = ['']  # current output candidates
    infos = []
    for step in range(task.steps):
        # generation
        if args.method_generate == 'sample':
            new_ys = [get_samples(task, x, y, args.n_generate_sample, prompt_sample=args.prompt_sample, stop=task.stops[step]) for y in ys]
        elif args.method_generate == 'propose':
            new_ys = [get_proposals(task, x, y) for y in ys]
        new_ys = list(itertools.chain(*new_ys))
        
        ####################
        expressions = {}
        for each in new_ys:
            lines = each.split('\n')
            last_line = lines[-2]

            numbers = last_line.split('left: ')[-1].split(')')[0]

            expressions[numbers] = []
            for i in range(len(lines) - 1):
                line = lines[i]
                expression = line.split('(')[0]
                expression = expression.replace(" ", "")
                expressions[numbers].append(expression)

        ####################

        ids = list(range(len(new_ys)))
        # evaluation
        if args.method_evaluate == 'vote':
            values = get_votes(task, x, new_ys, args.n_evaluate_sample)
        elif args.method_evaluate == 'value':
            values = get_values(task, x, new_ys, args.n_evaluate_sample, step = step, expressions = expressions)

        # selection
        if args.method_select == 'sample':
            ps = np.array(values) / sum(values)
            select_ids = np.random.choice(ids, size=args.n_select_sample, p=ps).tolist()
        elif args.method_select == 'greedy':
            select_ids = sorted(ids, key=lambda x: values[x], reverse=True)[:args.n_select_sample]
        select_new_ys = [new_ys[select_id] for select_id in select_ids]

        # # log
        # if to_print: 
        #     sorted_new_ys, sorted_values = zip(*sorted(zip(new_ys, values), key=lambda x: x[1], reverse=True))
        #     print(f'-- new_ys --: {sorted_new_ys}\n-- sol values --: {sorted_values}\n-- choices --: {select_new_ys}\n')
        
        infos.append({'step': step, 'x': x, 'ys': ys, 'new_ys': new_ys, 'values': values, 'select_new_ys': select_new_ys})
        ys = select_new_ys
    
    if to_print: 
        print(ys)
    return ys, {'steps': infos}

def naive_solve(args, task, idx, to_print=True):
    global gpt
    gpt = partial(gpt, model=args.backend, temperature=args.temperature)
    print(gpt)
    x = task.get_input(idx)  # input
    ys = get_samples(task, x, '', args.n_generate_sample, args.prompt_sample, stop=None)
    return ys, {}