import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
} from 'react-native';

const MainScreen: React.FC = () => {
  const features = [
    {id: 1, title: 'Vocabulary Builder', icon: '📚', description: 'Learn new words'},
    {id: 2, title: 'Grammar Lessons', icon: '📝', description: 'Master grammar rules'},
    {id: 3, title: 'Speaking Practice', icon: '🎤', description: 'Improve pronunciation'},
    {id: 4, title: 'Listening Exercises', icon: '👂', description: 'Train your ear'},
    {id: 5, title: 'Quiz Mode', icon: '🧠', description: 'Test your knowledge'},
    {id: 6, title: 'Progress Tracking', icon: '📊', description: 'Monitor your growth'},
  ];

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView}>
        <View style={styles.header}>
          <Text style={styles.welcomeText}>Welcome to</Text>
          <Text style={styles.title}>Language Learning</Text>
          <Text style={styles.subtitle}>Choose your learning path</Text>
        </View>

        <View style={styles.featuresContainer}>
          {features.map((feature) => (
            <TouchableOpacity key={feature.id} style={styles.featureCard}>
              <Text style={styles.featureIcon}>{feature.icon}</Text>
              <View style={styles.featureContent}>
                <Text style={styles.featureTitle}>{feature.title}</Text>
                <Text style={styles.featureDescription}>{feature.description}</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    backgroundColor: '#4facfe',
    paddingTop: 40,
    paddingBottom: 60,
    paddingHorizontal: 32,
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
  },
  welcomeText: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 16,
    fontWeight: '400',
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: 'white',
    marginBottom: 8,
    letterSpacing: -0.5,
  },
  subtitle: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 16,
    fontWeight: '400',
  },
  featuresContainer: {
    padding: 20,
    marginTop: -30,
  },
  featureCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  featureIcon: {
    fontSize: 32,
    marginRight: 16,
  },
  featureContent: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#235390',
    marginBottom: 4,
  },
  featureDescription: {
    fontSize: 14,
    color: '#666',
    fontWeight: '400',
  },
});

export default MainScreen;