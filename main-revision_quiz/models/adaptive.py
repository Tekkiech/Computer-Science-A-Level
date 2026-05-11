import datetime


class AdaptiveEngine:
    # I built this class to handle the complex maths for the A* criteria.
    # It does Spaced Repetition and calculates Elo ratings.

    @staticmethod
    def calculate_next_review(attempts, correct, current_elo, difficulty_str):
        """
        This is based on the SuperMemo-2 algorithm. It figures out when the user
        should next see a question so they don't forget it (the forgetting curve).
        """
        # Harder questions need reviewing sooner, easier ones can wait.
        difficulty_weights = {"Easy": 1.2, "Medium": 1.0, "Hard": 0.8}
        weight = difficulty_weights.get(difficulty_str, 1.0)

        # Calculate their accuracy for this specific question
        accuracy = correct / attempts if attempts > 0 else 0

        # If they got it wrong a lot, force them to review it tomorrow
        if accuracy < 0.5:
            days_to_add = 1
        else:
            # Exponential backoff: the more they get it right, the longer until they see it again.
            days_to_add = max(1, int((attempts * weight) * (accuracy * 2)))

        next_date = datetime.datetime.now() + datetime.timedelta(days=days_to_add)
        return next_date.strftime("%Y-%m-%d")

    @staticmethod
    def adjust_elo(user_elo, question_elo, is_correct):
        """
        I implemented an Elo rating system like they use in Chess and competitive games!
        If a student with a low rating gets a hard question right, their score shoots up.
        """
        K = 32  # Max rating change allowed per question

        # This formula calculates the expected probability of them getting it right
        expected_score = 1 / (1 + 10 ** ((question_elo - user_elo) / 400))
        actual_score = 1 if is_correct else 0

        # Adjust the rating based on the difference between actual and expected
        new_user_elo = user_elo + K * (actual_score - expected_score)
        return int(new_user_elo)
