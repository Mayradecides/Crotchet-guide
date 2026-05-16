

from stitch_counter import Project, Yarn, Hook, Stitches


def main():
  project_name = input("Enter your project name: ")
  crotchet = Project(project_name)
  yarn_obj = Yarn()
  hook_obj = Hook(crotchet)
  stitches_obj = Stitches(crotchet)

  while True:
    action = input("Type 'a' to add/update stitches, 's' to show count, or 'q' to quit: ")
    if action == 'a':
      stitches_obj.add_stitches()
    elif action == 's':
      stitches_obj.show_stitches()
    elif action == 'q':
      break
    else:
      print("Invalid input, please try again.")

if __name__ == "__main__":
  main()
