import React from 'react';
import { Ionicons, MaterialIcons, MaterialCommunityIcons } from '@expo/vector-icons';

// Icon mapping for consistent icon usage throughout the app
const iconMap = {
  // Navigation
  home: (props) => <Ionicons name="home" {...props} />,
  pathway: (props) => <MaterialIcons name="map" {...props} />,
  give: (props) => <MaterialIcons name="attach-money" {...props} />,
  groups: (props) => <MaterialIcons name="group" {...props} />,
  prayer: (props) => <MaterialIcons name="favorite" {...props} />,
  settings: (props) => <Ionicons name="settings" {...props} />,
  
  // Actions
  sunday: (props) => <MaterialIcons name="church" {...props} />,
  explore: (props) => <Ionicons name="compass" {...props} />,
  tv: (props) => <MaterialIcons name="tv" {...props} />,
  events: (props) => <MaterialIcons name="event" {...props} />,
  calendar: (props) => <MaterialIcons name="calendar-today" {...props} />,
  location: (props) => <Ionicons name="location" {...props} />,
  
  // Categories
  general: (props) => <MaterialIcons name="description" {...props} />,
  health: (props) => <MaterialIcons name="local-hospital" {...props} />,
  family: (props) => <MaterialIcons name="family-restroom" {...props} />,
  work: (props) => <MaterialIcons name="work" {...props} />,
  spiritual: (props) => <MaterialIcons name="auto-awesome" {...props} />,
  relationships: (props) => <MaterialIcons name="favorite" {...props} />,
  financial: (props) => <MaterialIcons name="account-balance-wallet" {...props} />,
  other: (props) => <MaterialIcons name="more-horiz" {...props} />,
  
  // Giving
  tithe: (props) => <MaterialIcons name="account-balance" {...props} />,
  offering: (props) => <MaterialIcons name="monetization-on" {...props} />,
  missions: (props) => <MaterialIcons name="flight" {...props} />,
  event: (props) => <MaterialIcons name="confirmation-number" {...props} />,
  
  // Explore
  resources: (props) => <MaterialIcons name="menu-book" {...props} />,
  search: (props) => <Ionicons name="search" {...props} />,
  music: (props) => <MaterialIcons name="music-note" {...props} />,
  meditation: (props) => <MaterialIcons name="self-improvement" {...props} />,
  community: (props) => <MaterialIcons name="people" {...props} />,
  
  // General
  arrowRight: (props) => <Ionicons name="chevron-forward" {...props} />,
  arrowBack: (props) => <Ionicons name="chevron-back" {...props} />,
  check: (props) => <Ionicons name="checkmark-circle" {...props} />,
  close: (props) => <Ionicons name="close" {...props} />,
  add: (props) => <Ionicons name="add" {...props} />,
  edit: (props) => <Ionicons name="create" {...props} />,
  delete: (props) => <MaterialIcons name="delete" {...props} />,
  empty: (props) => <MaterialIcons name="inbox" {...props} />,
};

export default function Icon({ name, size = 24, color = '#ffffff', style, ...props }) {
  const IconComponent = iconMap[name];
  
  if (!IconComponent) {
    console.warn(`Icon "${name}" not found in iconMap`);
    return <MaterialIcons name="help-outline" size={size} color={color} style={style} {...props} />;
  }
  
  return <IconComponent size={size} color={color} style={style} {...props} />;
}

