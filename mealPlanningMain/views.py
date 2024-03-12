from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.shortcuts import render, redirect
from mealPlanningMain.forms import SignUpForm, LoginForm
from django.db import connection
from .models import User
from django.contrib.auth.decorators import login_required
import joblib
import pandas as pd
import numpy as np
import random
import sklearn
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

model = joblib.load('/Users/yuanfanfan/代码日常/model/food_recommender.joblib')
label_encoder = joblib.load('/Users/yuanfanfan/代码日常/model/label_encoder.joblib')


# Create your views here.
def landing(request):
    return render(request, "landing.html")


def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            try:
                user = User.objects.get(username=username)
                if user.password == password:
                    login(request, user)
                    return redirect('profile')
                else:
                    messages.error(request, 'Password is incorrect')
            except User.DoesNotExist:
                messages.error(request, 'Username does not exist')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


@login_required
def profile(request):
    user = request.user

    def recommend_food(physical_activity, dietary_preferences, health_goals):
        recommended_food = []

        if physical_activity == "1":
            recommended_food.append("High-energy snacks like nuts and seeds")
        elif physical_activity == "2":
            recommended_food.append("Lean proteins like chicken or fish")
        elif physical_activity == "3":
            recommended_food.append("Complex carbohydrates like quinoa or brown rice")

        if dietary_preferences == "1":
            recommended_food.append("Plant-based proteins like tofu or lentils")
        elif dietary_preferences == "2":
            recommended_food.append("Lean meats and vegetables")
        elif dietary_preferences == "3":
            recommended_food.append("Fresh fruits and vegetables")
        elif dietary_preferences == "4":
            recommended_food.append("Raw nuts, seeds, and fruits")
        elif dietary_preferences == "5":
            recommended_food.append("Dairy alternatives like almond milk or soy yogurt")
        elif dietary_preferences == "6":
            recommended_food.append("Gluten-free grains like quinoa or buckwheat")
        elif dietary_preferences == "7":
            recommended_food.append("Seafood and plant-based proteins")
        elif dietary_preferences == "8":
            recommended_food.append("Healthy fats like avocados and nuts")

        if health_goals == "1":
            recommended_food.append("Lean proteins and vegetables for weight maintenance")
        elif health_goals == "2":
            recommended_food.append("Foods rich in omega-3 fatty acids like salmon or walnuts")
        elif health_goals == "3":
            recommended_food.append("Low-glycemic index foods like beans and whole grains for blood sugar control")

        return recommended_food

    physical_activity = user.physical_activity
    dietary_preferences = user.dietary_preferences
    health_goals = user.health_goals
    recommend_foods = recommend_food(physical_activity, dietary_preferences, health_goals)
    print(recommend_foods)
    context = {
        'user': user,
        'recommend_foods': recommend_foods
    }

    return render(request, 'profile.html', context)


@login_required
def mealplan(request):
    return render(request, 'meal-plans.html', {'user': request.user})


def personalInfo(request):
    if request.method == 'POST':
        user_age = request.POST.get('userage')
        user_gender = request.POST.get('usergender')
        physical_activity = request.POST.get('physical-activity')
        dietary_preferences = request.POST.get('dietary-preferences')
        health_goals = request.POST.get('health-goals')
        weight = request.POST.get('weight')
        height = request.POST.get('height')
        idea_weight = request.POST.get('ideaWeight')

        User.objects.update_or_create(
            defaults={
                'age': user_age,
                'gender': user_gender,
                'physical_activity': physical_activity,
                'dietary_preferences': dietary_preferences,
                'health_goals': health_goals,
                'weight': weight,
                'height': height,
                'idea_weight': idea_weight
            }
        )

        return redirect('personalInfo')
    return render(request, 'personal-info.html', {'user': request.user})


def recommend_food(request):
    df = pd.read_csv('/Users/yuanfanfan/updated_recipes.csv', low_memory=False)
    user_preferences = {
        'Calories': 200,
        'FatContent': 10,
        'ProteinContent': 50,
        'CarbohydrateContent': 20,
        'SodiumContent': 5,
        'SugarContent': 5
    }

    user_input = pd.DataFrame([user_preferences])

    prediction = model.predict(user_input)

    recommended_category = label_encoder.inverse_transform(prediction)[0]

    matching_foods = df[df['Category'] == recommended_category]

    if not matching_foods.empty:
        recommended_food = matching_foods.sample(n=1).iloc[0]
        food_name = recommended_food['Name']
    else:
        food_name = "No matching food found."

    return JsonResponse({'recommended_category': recommended_category, 'recommended_food': food_name})


def test(request):
    user = request.user

    def generate_nutrition_standards(age, weight, physical_activity):
        default_nutrition_standards = {
            'ProteinContent': (50, 150),
            'FatContent': (20, 70),
            'CarbohydrateContent': (130, 300),
            'Calories': (1800, 2500)
        }

        protein_upper_limit = min(2.2 * weight, 150)
        age_adjustment = 0
        if age > 50:
            age_adjustment = 200
        calorie_lower_limit = max(1800 - age_adjustment, 1200)
        calorie_upper_limit = min(2500 + age_adjustment, 3000)

        if physical_activity == 1:
            calorie_upper_limit -= 200
        elif physical_activity == 2:
            calorie_upper_limit += 200

        personalized_nutrition_standards = {
            'ProteinContent': (50, protein_upper_limit),
            'FatContent': (20, 70),
            'CarbohydrateContent': (130, 300),
            'Calories': (calorie_lower_limit, calorie_upper_limit)
        }

        return personalized_nutrition_standards

    personalized_nutrition_standards = generate_nutrition_standards(user.age, user.weight, user.physical_activity)
    print("Personalized Nutrition Standards:")
    print(personalized_nutrition_standards)

    # Read and load the dataset
    df = pd.read_csv('/Users/yuanfanfan/updated_categories_recipes.csv', low_memory=False)

    # Converting data types
    numeric_columns = ['Calories', 'FatContent', 'SaturatedFatContent', 'CholesterolContent',
                       'SodiumContent', 'CarbohydrateContent', 'FiberContent', 'SugarContent', 'ProteinContent']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Remove any rows containing null values for clustering analysis
    df.dropna(subset=numeric_columns, inplace=True)

    # Initialization and standardization
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(df[numeric_columns])

    # Use KMeans to clustering
    kmeans = KMeans(n_clusters=10, random_state=42)
    df['Cluster'] = kmeans.fit_predict(features_scaled)

    def check_nutrition_balance(total_nutrition, nutrition_standards):
        nutrition_balance = all(
            nutrition_standards[key][0] <= total_nutrition[key] <= nutrition_standards[key][1] for key in
            nutrition_standards)
        return nutrition_balance

    def generate_food_recommendations(df, age, weight, physical_activity):
        nutrition_balance = False
        attempt = 0
        while not nutrition_balance:
            attempt += 1
            # random choose a cluster
            selected_cluster = np.random.choice(df['Cluster'].unique())
            cluster_meals = df[df['Cluster'] == selected_cluster]
            breakfast_meals = cluster_meals[cluster_meals['Meal'] == 'Breakfast']
            lunch_meals = cluster_meals[cluster_meals['Meal'] == 'Lunch']
            dinner_meals = cluster_meals[cluster_meals['Meal'] == 'Dinner']
            if breakfast_meals.empty or lunch_meals.empty or dinner_meals.empty:
                print("One or more meal categories have no samples. Skipping this attempt.")
                continue
            # Confirmation that the sample size is 1 for each meal category
            breakfast_sample = breakfast_meals.sample(n=1)
            lunch_sample = lunch_meals.sample(n=1)
            dinner_sample = dinner_meals.sample(n=1)
            # Randomly selected samples can be repeated if the sample size is less than 3
            recommended_meals = pd.concat([breakfast_sample, lunch_sample, dinner_sample])
            # Calculation of total nutrient intake
            total_nutrition = recommended_meals[
                ['ProteinContent', 'FatContent', 'CarbohydrateContent', 'Calories']].sum()

            personalized_nutrition_standards = generate_nutrition_standards(age, weight, physical_activity)

            # Check that nutrition is within balanced limits
            nutrition_balance = check_nutrition_balance(total_nutrition, personalized_nutrition_standards)
            print(f"attempt #{attempt}")
            print("Recommended food combinations:")
            print(recommended_meals[['Name', 'ProteinContent', 'FatContent', 'CarbohydrateContent', 'Calories']])
            print("\nTotal nutrient intake for three selected meals per day:")
            print(total_nutrition)
            print("\nWhether the nutrition is balanced:", "Yes" if nutrition_balance else "No")
            print("-" * 50)

            if nutrition_balance:
                print("Find food combinations that are nutritionally balanced!")

                return recommended_meals[
                    ['Name', 'ProteinContent', 'FatContent', 'CarbohydrateContent',
                     'Calories']], total_nutrition, nutrition_balance
            else:
                print("Keep looking...")

    recommended_meals, total_nutrition, nutrition_balance = generate_food_recommendations(df, user.age, user.weight,
                                                                                          user.physical_activity)
    return render(request, 'test.html', {'rm': recommended_meals.to_html(), 'total_nutrition': total_nutrition,
                                         'nutrition_balance': nutrition_balance})
