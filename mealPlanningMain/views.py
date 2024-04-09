from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect

from AI_Powered_Meal_Planning_App import settings
from mealPlanningMain.forms import SignUpForm, LoginForm
from django.db import connection
from .models import User
from django.contrib.auth.decorators import login_required
import joblib
from django.templatetags.static import static
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from django.contrib.auth import logout

import random
import sklearn
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

model = joblib.load('food_prediction_model.joblib')


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


def user_logout(request):
    logout(request)
    return redirect('/')


def about(request):
    return render(request, 'about.html')


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
    user = request.user
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
            id=user.id,
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
        return redirect('test')
    return render(request, 'personal-info.html', {'user': request.user})


def upload_file(request):
    if request.method == 'POST' and request.FILES['csv-input']:
        print("11111")
        csv_file = request.FILES['csv-input']

        fs = FileSystemStorage()

        file_name = 'weekly-meal-plan.csv'
        if fs.exists(file_name):
            fs.delete(file_name)

        file_path = fs.save(file_name, csv_file)

        file_url = fs.url(file_path)

        return redirect(predict)

    return HttpResponse('Failed to upload file')


def generate_charts(daily_sums):
    charts_url = {}
    print("Generating charts for days:", daily_sums.keys())  # 测试输出1：检查哪些天的数据将被处理
    for day, sums in daily_sums.items():
        labels = ['Calories', 'Fat Content', 'Carbohydrate Content', 'Protein Content']
        sizes = [sums['Calories'], sums['FatContent'], sums['CarbohydrateContent'], sums['ProteinContent']]

        plt.figure(figsize=(6, 6))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')
        pie_path = os.path.join('mealPlanningMain/static/images', f'pie_chart_{day}.png')
        plt.savefig(pie_path)
        plt.close()

        print(f"Saved pie chart for {day} at: {pie_path}")

        plt.figure(figsize=(8, 6))
        categories = range(len(labels))
        plt.bar(categories, sizes, color=['red', 'blue', 'yellow', 'green'])
        plt.xticks(categories, labels)
        bar_path = os.path.join('mealPlanningMain/static/images', f'bar_chart_{day}.png')
        plt.savefig(bar_path)
        plt.close()

        print(f"Saved bar chart for {day} at: {bar_path}")

        charts_url[day] = {
            'pie_chart_url': static(f'mealPlanningMain/images/pie_chart_{day}.png'),
            'bar_chart_url': static(f'mealPlanningMain/images/bar_chart_{day}.png')
        }

    return charts_url


def predict(request):
    csv_file_path = 'weekly-meal-plan.csv'

    df = pd.read_csv(csv_file_path)
    print("CSV loaded. Number of rows:", len(df))

    food_names = df['foodname'].tolist()

    predictions = model.predict(food_names)
    print("Predictions made for food names.")

    df['Calories'], df['FatContent'], df['CarbohydrateContent'], df['ProteinContent'] = zip(*predictions)
    daily_sums = df.groupby('day')[['Calories', 'FatContent', 'CarbohydrateContent', 'ProteinContent']].sum().round(2)

    weekdays_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_sums = daily_sums.reindex(weekdays_order)

    daily_sums_dict = daily_sums.to_dict(orient='index')
    print("Daily sums calculated.")

    charts_url = generate_charts(daily_sums_dict)

    return render(request, 'meal-plans-result.html', {'daily_sums': daily_sums_dict, 'charts_url': charts_url})


def test(request):
    user = request.user

    def user_profile(dietary_preferences, health_goals):
        recommended_food = []

        if dietary_preferences == "1":
            recommended_food.append(
                "You are Vegan. Your food will focuses on plant-based foods including vegetables, fruits, beans, grains, nuts, and seeds. ")
        elif dietary_preferences == "2":
            recommended_food.append(
                "You are Paleo. Your food will emulates ancient human diets consisting mainly of meat, fish, nuts, leafy greens, regional veggies, and seeds")
        elif dietary_preferences == "3":
            recommended_food.append(
                "Lactose Intolerance, Your food will offers meals without lactose, catering to those who are lactose intolerant. ")
        elif dietary_preferences == "4":
            recommended_food.append(
                "You like Raw Food. Your food will comprises unprocessed and uncooked plant foods, such as fresh fruits and vegetables, nuts, seeds, and sprouted grains.")
        elif dietary_preferences == "5":
            recommended_food.append("Dairy-free. Your food will provides meals that do not contain dairy products.")
        elif dietary_preferences == "6":
            recommended_food.append(
                "You are Vegetarian. Your food will includes meals that may contain eggs and dairy but does not include meat, poultry, or fish.")
        elif dietary_preferences == "7":
            recommended_food.append(
                "You are Pescatarian. Your food will excludes all other forms of meat and poultry, focusing on fish, fruits, vegetables, grains, and nuts.")
        elif dietary_preferences == "8":
            recommended_food.append(
                "You are Keto. Your food will contain a high-fat, adequate-protein, low-carbohydrate diet that helps to burn fats more efficiently. Includes meat, fish, eggs, cheese, and low-carb vegetables.")
        else:
            recommended_food.append(
                "You have no dietary preferences.")

        if health_goals == "10":
            recommended_food.append("Loss Weight")
        elif health_goals == "6":
            recommended_food.append("Supporting muscle growth and strength.")
        elif health_goals == "5":
            recommended_food.append("Building and maintaining strong bones.")
        elif health_goals == "8":
            recommended_food.append("Stress Reduction and Enhancing Mood")
        elif health_goals == "12":
            recommended_food.append("Improving Physical Performance")

        return recommended_food

    def generate_nutrition_standards(age, weight, physical_activity):
        # default_nutrition_standards = {
        #     'ProteinContent': (50, 150),
        #     'FatContent': (20, 70),
        #     'CarbohydrateContent': (130, 300),
        #     'Calories': (1800, 2500)
        # }
        #
        # protein_upper_limit = min(2.2 * weight, 150)
        # age_adjustment = 0
        # if age > 50:
        #     age_adjustment = 200
        # calorie_lower_limit = max(1000 - age_adjustment, 1000)
        # calorie_upper_limit = min(2500 + age_adjustment, 3000)
        #
        # if physical_activity == 1:
        #     calorie_upper_limit -= 200
        # elif physical_activity == 2:
        #     calorie_upper_limit += 200

        personalized_nutrition_standards = {
            'Proteins': (0, 100000),
            'Fats': (0, 100000),
            'Carbohydrates': (0, 100000),
            'Calories': (0, 100000)
        }

        return personalized_nutrition_standards

    personalized_nutrition_standards = generate_nutrition_standards(user.age, user.weight, user.physical_activity)
    print("Personalized Nutrition Standards:")
    print(personalized_nutrition_standards)

    df = pd.read_csv('Meal_data.csv', low_memory=False)

    numeric_columns = ['Calories', 'Fats', 'Proteins', 'Carbohydrates']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df.dropna(subset=numeric_columns, inplace=True)

    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(df[numeric_columns])

    kmeans = KMeans(n_clusters=10, random_state=42)
    df['Cluster'] = kmeans.fit_predict(features_scaled)

    def check_nutrition_balance(total_nutrition, nutrition_standards):
        nutrition_balance = all(
            nutrition_standards[key][0] <= total_nutrition[key] <= nutrition_standards[key][1] for key in
            nutrition_standards)
        return nutrition_balance

    def generate_food_recommendations(df, age, weight, ideal_weight, physical_activity, dietary_preferences,
                                      health_goals):
        nutrition_balance = False
        attempt = 0

        # weight_goal = 'Lose' if weight > ideal_weight else 'Gain'

        while not nutrition_balance:
            attempt += 1
            selected_cluster = np.random.choice(df['Cluster'].unique())

            if dietary_preferences == "1":
                cluster_meals = df[(df['Cluster'] == selected_cluster) & (df['Vegan'] == 'Yes')]
            elif dietary_preferences == "2":
                cluster_meals = df[(df['Cluster'] == selected_cluster) & (df['Paleo'] == 'Yes')]
            elif dietary_preferences == "3":
                cluster_meals = df[(df['Cluster'] == selected_cluster) & (df['Lactose'] == 'Yes')]
            elif dietary_preferences == "4":
                cluster_meals = df[(df['Cluster'] == selected_cluster) & (df['Raw'] == 'Yes')]
            elif dietary_preferences == "5":
                cluster_meals = df[(df['Cluster'] == selected_cluster) & (df['Dairy-Free'] == 'Yes')]
            elif dietary_preferences == "6":
                cluster_meals = df[(df['Cluster'] == selected_cluster) & (df['Vegetarian'] == 'Yes')]
            elif dietary_preferences == "7":
                cluster_meals = df[(df['Cluster'] == selected_cluster) & (df['Pescatarian'] == 'Yes')]
            # elif dietary_preferences == "8":
            #     cluster_meals = df[(df['Cluster'] == selected_cluster) & (df['Keto'] == 'Yes')]
            else:
                cluster_meals = df[df['Cluster'] == selected_cluster]

            # if weight_goal == 'Lose':
            #     cluster_meals = df[(df['Cluster'] == selected_cluster) & (df['Loss'] == 'Yes')]
            # elif weight_goal == 'Gain':
            #     cluster_meals = df[(df['Cluster'] == selected_cluster) & (df['Loss'] == 'No')]

            if health_goals == "10":
                cluster_meals = cluster_meals[cluster_meals['Loss'] == 'Yes']
            elif health_goals == "6" or health_goals == "12" or health_goals == "5":
                cluster_meals = cluster_meals[cluster_meals['Muscle'] == 'Yes']
            # elif health_goals == 3:
            #     cluster_meals = cluster_meals[cluster_meals['HighProtein'] == 'Yes']

            breakfast_meals = cluster_meals[cluster_meals['Meal'] == 'Breakfast']
            lunch_meals = cluster_meals[cluster_meals['Meal'] == 'Lunch']
            dinner_meals = cluster_meals[cluster_meals['Meal'] == 'Dinner']

            if breakfast_meals.empty or lunch_meals.empty or dinner_meals.empty:
                continue

            breakfast_sample = breakfast_meals.sample(n=1)
            lunch_sample = lunch_meals.sample(n=1)
            dinner_sample = dinner_meals.sample(n=1)
            recommended_meals = pd.concat([breakfast_sample, lunch_sample, dinner_sample])

            total_nutrition = recommended_meals[['Proteins', 'Fats', 'Carbohydrates', 'Calories']].sum().to_dict()

            personalized_nutrition_standards = generate_nutrition_standards(age, weight, physical_activity)
            nutrition_balance = check_nutrition_balance(total_nutrition, personalized_nutrition_standards)

            if nutrition_balance:
                return recommended_meals[
                    ['Name', 'Proteins', 'Fats', 'Carbohydrates', 'Calories', 'Meal',
                     'PortionSize']], total_nutrition, nutrition_balance

    recommended_meals = {}
    total_nutrition = {}
    nutrition_balance = {}
    for day in range(1, 8):
        print(f"Day {day}")
        rec_meals, tot_nutrition, nutri_balance = generate_food_recommendations(df,
                                                                                user.age,
                                                                                user.weight,
                                                                                user.idea_weight,
                                                                                user.physical_activity,
                                                                                user.dietary_preferences,
                                                                                user.health_goals
                                                                                )
        print("\n")
        recommended_meals[day] = rec_meals
        total_nutrition[day] = tot_nutrition
        nutrition_balance[day] = nutri_balance
    # if request.method == 'POST':
    #     user_age = request.POST.get('userage')
    #     user_gender = request.POST.get('usergender')
    #     physical_activity = request.POST.get('physical-activity')
    #     dietary_preferences = request.POST.get('dietary-preferences')
    #     health_goals = request.POST.get('health-goals')
    #     weight = request.POST.get('weight')
    #     height = request.POST.get('height')
    #     idea_weight = request.POST.get('ideaWeight')
    #     print(user_age, physical_activity)
    #     User.objects.update_or_create(
    #         defaults={
    #             'age': user_age,
    #             'gender': user_gender,
    #             'physical_activity': physical_activity,
    #             'dietary_preferences': dietary_preferences,
    #             'health_goals': health_goals,
    #             'weight': weight,
    #             'height': height,
    #             'idea_weight': idea_weight
    #         }
    #     )
    recommend_foods = user_profile(user.dietary_preferences, user.health_goals)
    print(recommend_foods)
    return render(request, 'test.html', {'rm': recommended_meals, 'total_nutrition': total_nutrition,
                                         'nutrition_balance': nutrition_balance, 'recommend_foods': recommend_foods})
