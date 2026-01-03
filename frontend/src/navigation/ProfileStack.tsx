import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import UserScreen from '../screens/user/UserScreen';
import EditProfileScreen from '../screens/user/EditProfileScreen';

const ProfileStack = createStackNavigator();

const ProfileNavigator = () => {
    return (
        <ProfileStack.Navigator screenOptions={{ headerShown: false }}>
            <ProfileStack.Screen name="UserProfile" component={UserScreen} />
            <ProfileStack.Screen
                name="EditProfile"
                component={EditProfileScreen}
                options={{ headerShown: true, title: "Edycja Profilu" }}
            />
        </ProfileStack.Navigator>
    );
};

export default ProfileNavigator;
