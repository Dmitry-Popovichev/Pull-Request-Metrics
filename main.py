import math, sys

def very_long_function_name(   variable_one, variable_two,
    variable_three,variable_four):
    # This is a messy list
    my_list = [1,2,3,
        4,5,6,
          7,8,9]
    
    # This dictionary has inconsistent spacing
    my_dict = {'key1':'value1',    "key2"  :  "value2", "key3":"value3"}

    # Poorly formatted math and long strings
    result = (variable_one+variable_two+variable_three+variable_four) * math.pi
    print("This is a very long string that should probably be broken up into multiple lines if it exceeds the line length limit of eighty-eight characters")

    return result

if __name__ == "__main__":
    # Inconsistent indentation and extra whitespace
    print (  very_long_function_name(1, 2, 3, 4)  )
