from rest_framework import serializers
import re


class UserDataSerializer(serializers.Serializer):
    """
    Serializer for user data submission.
    
    Validates and serializes user input data including name, email, and age.
    """
    name = serializers.CharField(
        max_length=100,
        required=True,
        help_text="User's full name"
    )
    email = serializers.EmailField(
        required=True,
        help_text="User's email address"
    )
    age = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=150,
        help_text="User's age (1-150)"
    )
    
    def validate_name(self, value):
        """
        Validate that name contains only letters, spaces, hyphens, and apostrophes.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty or only whitespace.")
        
        if not re.match(r"^[a-zA-Z\s\-']+$", value):
            raise serializers.ValidationError(
                "Name can only contain letters, spaces, hyphens, and apostrophes."
            )
        
        return value.strip()
    
    def validate_email(self, value):
        """
        Additional email validation beyond default EmailField validation.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Email cannot be empty.")
        
        return value.strip().lower()
    
    def validate_age(self, value):
        """
        Validate age is within reasonable bounds.
        """
        if value < 1 or value > 150:
            raise serializers.ValidationError("Age must be between 1 and 150.")
        
        return value
