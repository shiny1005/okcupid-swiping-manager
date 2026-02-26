"""
GraphQL query and mutation strings for OkCupid (e2p-okapi.api.okcupid.com/graphql/).
Most of these come directly from DevTools → Network → request Payload → `query`.
"""

# Step 1: Fetch stacks menu – returns stack ids; user ids are in data.match.user.id
WEB_INITIAL_STACKS_MENU_QUERY = """fragment ProfileHighlights on StackMatch {
  profileHighlights {
    ... on PhotoHighlight {
      id
      caption
      url
      __typename
    }
    __typename
  }
  __typename
}

fragment MinimalStackMatchFragment on StackMatch {
  stream
  displayStream
  targetLikesSender
  selfieVerifiedStatus
  match {
    user {
      id
      __typename
    }
    __typename
  }
  ...ProfileHighlights
  __typename
}

fragment PromotedQuestionPromptFragment on PromotedQuestionPrompt {
  promotedQuestionId
  __typename
}

fragment MinimalStackFragment on Stack {
  id
  status
  votesRemaining
  expireTime
  badge
  data {
    ...MinimalStackMatchFragment
    ...PromotedQuestionPromptFragment
    __typename
  }
  __typename
}

query WebInitialStacksMenu {
  me {
    id
    stacks {
      ...MinimalStackFragment
      __typename
    }
    __typename
  }
}"""

# Step 2: Fetch full user details by ids from WebInitialStacksMenu
# Path: /graphql/WebStackUsers, variables: {userIds: ["id1", "id2", ...]}
WEB_STACK_USERS_QUERY = """fragment PhotoInfo on Photo {
  id
  caption
  original
  square60
  square82
  square100
  square120
  square160
  square225
  square400
  square800
  __typename
}

fragment UserPrimaryImagesFragment on User {
  primaryImage {
    id
    caption
    original
    square60
    square82
    square100
    square120
    square160
    square225
    square400
    square800
    __typename
  }
  __typename
}

fragment WiwSentencePreferences on User {
  globalPreferences {
    gender {
      values
      __typename
    }
    relationshipType {
      values
      __typename
    }
    connectionType {
      values
      __typename
    }
    __typename
  }
  __typename
}

fragment ProfileCommentAttachment on Attachment {
  ... on ProfileCommentPhoto {
    type
    photo {
      id
      square800
      __typename
    }
    __typename
  }
  ... on ProfileCommentInstagramPhoto {
    type
    instagramPhoto {
      caption
      original
      __typename
    }
    __typename
  }
  ... on ProfileCommentEssay {
    type
    essayTitle
    essayText
    __typename
  }
  __typename
}

fragment FirstMessageFragment on Match {
  senderLikes
  senderPassed
  senderVote
  firstMessage {
    id
    threadId
    text
    attachments {
      ...ProfileCommentAttachment
      __typename
    }
    __typename
  }
  __typename
}

fragment SelfDetails on User {
  children
  relationshipStatus
  relationshipType
  smoking
  weed
  drinking
  diet
  pets
  ethnicity
  politics
  bodyType
  height
  astrologicalSign
  knownLanguages
  pronounCategory
  customPronouns
  genders
  orientations
  identityTags
  realname
  religion {
    value
    modifier
    __typename
  }
  religiousBackground
  shabbatRoutine
  kosherHabits
  occupation {
    title
    status
    employer
    __typename
  }
  education {
    level
    school {
      name
      __typename
    }
    __typename
  }
  __typename
}

fragment Badges on User {
  badges {
    name
    __typename
  }
  __typename
}

fragment EssayFragment on Essay {
  id
  groupId
  groupTitle
  isPassion
  title
  placeholder
  rawContent
  processedContent
  __typename
}

fragment MatchFragment on Match {
  ...FirstMessageFragment
  matchPercent
  targetLikes
  targetVote
  senderLikes
  senderVote
  targetMessageTime
  targetLikeViaSpotlight
  targetLikeViaSuperBoost
  user {
    id
    displayname
    username
    age
    hasPhotos
    ...UserPrimaryImagesFragment
    userLocation {
      id
      publicName
      __typename
    }
    photos {
      ...PhotoInfo
      __typename
    }
    essaysWithUniqueIds {
      ...EssayFragment
      __typename
    }
    ...WiwSentencePreferences
    ...SelfDetails
    ...Badges
    __typename
  }
  __typename
}

query WebStackUsers($userIds: [String!]!) {
  me {
    id
    matches(ids: $userIds, includeAllQuestionHighlights: true) {
      ...MatchFragment
      __typename
    }
    __typename
  }
}
"""

# Single like/pass. Copy the mutation from the request when you click Like or Pass.
SWIPE_MUTATION = """
mutation WebUserVote($input: UserVoteInput!) {\n  userVote(input: $input) {\n    success\n    voteResults {\n      success\n      statusCode\n      isMutualLike\n      isViaSpotlight\n      isViaSuperBoost\n      votesRemainingInSource\n      __typename\n    }\n    shouldTrackLikesCapReached\n    likesRemaining\n    likesCapResetTime\n    __typename\n  }\n}
"""

# Variable names in the real API may differ (e.g. userId, vote). Adjust in swipe.py when you capture the payload.


# Chat / messaging GraphQL operations

WEB_ME_QUERY = """query WebMe {
  session {
    guestId
    isStaff
    isInEU
    __typename
  }
  me {
    id
    displayname
    age
    userLocation {
      id
      fullName
      publicName
      countryCode
      stateCode
      __typename
    }
    joinDate
    premiums {
      ALIST_BASIC
      ALIST_PREMIUM
      ALIST_PREMIUM_PLUS
      ADFREE
      VIEW_VOTES
      INCOGNITO_BUNDLE
      READ_RECEIPTS
      SEE_PUBLIC_QUESTIONS
      INTROS
      UNLIMITED_REWINDS
      __typename
    }
    __typename
  }
}"""


WEB_GET_MESSAGES_MAIN_QUERY = """fragment UserPrimaryImagesFragment on User {
  primaryImage {
    id
    caption
    original
    square60
    square82
    square100
    square120
    square160
    square225
    square400
    square800
    __typename
  }
  __typename
}

fragment ConversationMatch on Match {
  senderLikeTime
  senderVote
  targetLikeTime
  targetVote
  targetLikeViaSpotlight
  targetLikeViaSuperBoost
  senderMessageTime
  targetMessageTime
  matchPercent
  user {
    id
    displayname
    username
    age
    isOnline
    ...UserPrimaryImagesFragment
    __typename
  }
  __typename
}

fragment ConversationFragment on Conversation {
  threadid
  time
  isUnread
  sentTime
  receivedTime
  status
  correspondent {
    ...ConversationMatch
    __typename
  }
  snippet {
    text
    sender {
      id
      __typename
    }
    __typename
  }
  attachmentPreviews {
    ... on ReactionUpdate {
      originalMessage
      reaction
      updateType
      __typename
    }
    ... on GifAttachmentPreview {
      id
      __typename
    }
    ... on PhotoAttachmentPreview {
      id
      __typename
    }
    __typename
  }
  __typename
}

fragment MutualMatchFragment on MutualMatch {
  status
  isUnread
  match {
    ...ConversationMatch
    __typename
  }
  __typename
}

fragment NotificationCountsFragment on User {
  notificationCounts {
    likesMutual
    likesIncoming
    likesAndViews
    messages
    intros
    __typename
  }
  __typename
}

fragment ConversationsAndMatches on User {
  ...NotificationCountsFragment
  conversationsAndMatches(filter: $filter, after: $after) {
    data {
      ...ConversationFragment
      ...MutualMatchFragment
      __typename
    }
    pageInfo {
      hasMore
      after
      total
      __typename
    }
    __typename
  }
  __typename
}

query WebGetMessagesMain($userid: String!, $filter: ConversationsAndMatchesFilter!, $after: String) {
  user(id: $userid) {
    id
    ...ConversationsAndMatches
    __typename
  }
}"""


WEB_CONVERSATION_THREAD_QUERY = """fragment GifFragment on GifMedia {
  width
  height
  url
  __typename
}

fragment PhotoInfo on Photo {
  id
  caption
  original
  square60
  square82
  square100
  square120
  square160
  square225
  square400
  square800
  __typename
}

fragment MessageAttachmentFragment on Attachment {
  __typename
  ... on GifResult {
    id
    vendor
    gif {
      ...GifFragment
      __typename
    }
    medium {
      ...GifFragment
      __typename
    }
    tiny {
      ...GifFragment
      __typename
    }
    nano {
      ...GifFragment
      __typename
    }
    __typename
  }
  ... on ProfileCommentPhoto {
    type
    photo {
      ...PhotoInfo
      __typename
    }
    __typename
  }
  ... on ProfileCommentInstagramPhoto {
    type
    instagramPhoto {
      caption
      original
      __typename
    }
    __typename
  }
  ... on ProfileCommentEssay {
    type
    essayTitle
    essayText
    __typename
  }
  ... on ReactionUpdate {
    updateType
    __typename
  }
  ... on Reaction {
    reaction
    senderId
    __typename
  }
}

fragment MessageAttachmentsFragment on Message {
  attachments {
    ...MessageAttachmentFragment
    __typename
  }
  __typename
}

fragment CorrespondentFragment on Match {
  targetLikes
  isMutualLike
  targetVote
  senderVote
  matchPercent
  targetLikeViaSuperBoost
  targetLikeViaSpotlight
  senderBlocked
  firstMessage {
    text
    __typename
  }
  user {
    id
    displayname
    isOnline
    photos {
      ...PhotoInfo
      __typename
    }
    __typename
  }
  firstMessage {
    id
    text
    threadId
    ...MessageAttachmentsFragment
    __typename
  }
  __typename
}

fragment MessageFragment on Message {
  id
  senderId
  threadId
  text
  time
  readTime
  ...MessageAttachmentsFragment
  __typename
}

fragment ConversationThreadFragment on ConversationThread {
  id
  status
  pageInfo {
    hasMore
    total
    __typename
  }
  showScammerWarning
  showContentWarning
  showFeedbackAgentWarning
  showFullInboxWarning
  canMessage
  isReadReceiptActivated
  correspondent {
    ...CorrespondentFragment
    __typename
  }
  messages {
    ...MessageFragment
    __typename
  }
  __typename
}

query WebConversationThread($targetId: ID!, $limit: Int, $before: String, $isPolled: Boolean) {
  me {
    id
    conversationThread(
      targetId: $targetId
      limit: $limit
      before: $before
      isPolled: $isPolled
    ) {
      ...ConversationThreadFragment
      __typename
    }
    __typename
  }
}"""


WEB_CONVERSATION_MESSAGE_SEND_MUTATION = """mutation WebConversationMessageSend($input: ConversationMessageSendInput!) {
  conversationMessageSend(input: $input) {
    success
    messageId
    nway
    threadId
    errorCode
    __typename
  }
}"""


WEB_SETTINGS_PAGE_QUERY = """fragment BirthdayFragment on User {
  birthdate {
    year
    month
    day
    __typename
  }
  __typename
}

fragment UnitPreferenceFragment on User {
  unitPreference
  __typename
}

fragment Email on User {
  emailAddress
  __typename
}

fragment Realname on User {
  realname
  displayname
  __typename
}

fragment PhoneNumber on User {
  phoneNumber
  __typename
}

fragment ResetPassword on User {
  emailAddress
  __typename
}

fragment SettingsLocation on User {
  userLocation {
    id
    countryCode
    stateCode
    fullName
    publicName
    __typename
  }
  __typename
}

fragment CouponFragment on Coupon {
  redeemedDate
  couponPercentage
  subscriptionId
  formattedInitialSubtotalPrice
  formattedDiscountedSubtotalPrice
  taxType
  isUsed
  __typename
}

fragment ActiveSubscriptionsFragment on User {
  billingActiveSubscriptions {
    id
    subscription {
      id
      paymentType
      originalPurchaseDate
      expirationDate
      billingDate
      billingStatus
      coupon {
        ...CouponFragment
        __typename
      }
      __typename
    }
    plan {
      id
      productType
      productSubType: productSubtype
      price
      period
      periodType
      __typename
    }
    __typename
  }
  __typename
}

query WebSettingsPage {
  me {
    id
    ...BirthdayFragment
    ...UnitPreferenceFragment
    ...Email
    ...Realname
    ...PhoneNumber
    ...ResetPassword
    ...SettingsLocation
    ...ActiveSubscriptionsFragment
    __typename
  }
}"""


