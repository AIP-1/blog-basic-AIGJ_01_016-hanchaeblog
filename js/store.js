/**
 * 데이터 저장소: 서버 API 를 부르는 얇은 묶음 (API 명세서 4장)
 * 응답 모양은 명세서 그대로 돌려준다. 화면은 이 파일의 함수만 부른다.
 *
 * PostSummary { blog: { address, name }, no, title, excerpt, thumbnail_url, category: { id, name } | null,
 *               topic: { slug, name } | null, published_at, like_count, comment_count, visibility, view_count? }
 */
const Store = (function () {
  const enc = encodeURIComponent;
  const blogUrl = (address) => `/api/blogs/${enc(address)}`;
  const postUrl = (address, no) => `${blogUrl(address)}/posts/${no}`;

  const ADDRESS_REASONS = {
    INVALID: '영문 소문자 · 숫자 · 하이픈으로 4~32자를 써 주세요. 하이픈으로 시작하거나 끝날 수 없어요.',
    RESERVED: '서비스가 쓰는 주소라 쓸 수 없어요.',
    TAKEN: '이미 있거나 예약된 주소예요.',
  };

  // 없거나 볼 수 없으면(404) null
  async function orNull(promise) {
    try {
      return await promise;
    } catch (err) {
      if (err.status === 404) return null;
      throw err;
    }
  }

  function query(params) {
    const search = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') search.set(key, value);
    });
    const text = search.toString();
    return text ? `?${text}` : '';
  }

  // ----- 골목 -----
  let topicsCache = null;
  async function getTopics() {
    if (!topicsCache) topicsCache = await Api.get('/api/topics');
    return topicsCache;
  }

  // ----- 한채 -----
  const getBlog = (address) => (address ? orNull(Api.get(blogUrl(address))) : Promise.resolve(null));

  async function getMyBlog() {
    const user = await Auth.currentUser();
    return user && user.blog_address ? getBlog(user.blog_address) : null;
  }

  async function checkAddress(address) {
    const result = await Api.get(`/api/blogs/address-available${query({ address })}`);
    return result.available
      ? { available: true }
      : { available: false, reason: ADDRESS_REASONS[result.reason] || '쓸 수 없는 주소예요.' };
  }

  async function createBlog({ address, name, description }) {
    const blog = await Api.post('/api/blogs', { address, name, description });
    await Auth.refresh(); // 내 정보의 blog_address 가 생겼다
    return blog;
  }

  // 한채 이름 · 주인 소개 바꾸기 (주인만) → 바뀐 대문 정보
  const updateBlog = (address, data) => Api.patch(blogUrl(address), data);

  // { subscribed, subscriber_count }
  const setNeighbor = (address, on) => (on
    ? Api.put(`${blogUrl(address)}/subscription`)
    : Api.delete(`${blogUrl(address)}/subscription`));

  // ----- 방 · 태그 -----
  // { total_count, rooms: [{ id, name, post_count }], uncategorized_count }
  const getRooms = (address) => Api.get(`${blogUrl(address)}/categories`);
  const addRoom = (address, name) => Api.post(`${blogUrl(address)}/categories`, { name });
  // [{ name, post_count }]
  const getTags = (address) => Api.get(`${blogUrl(address)}/tags`);

  // ----- 기록 목록 -----
  // filter: { category: id | 'none', tag, q, page } → { items, page, size, total, total_pages }
  const listPosts = (address, filter = {}) => Api.get(`${blogUrl(address)}/posts${query(filter)}`);

  // 마을 목록 (커서) → { items, next_cursor }
  const newPosts = ({ cursor, limit } = {}) => Api.get(`/api/home/new-posts${query({ cursor, limit })}`);
  const topicPosts = (slug, { cursor, limit } = {}) => Api.get(`/api/topics/${enc(slug)}/posts${query({ cursor, limit })}`);
  const neighborFeed = ({ cursor, limit } = {}) => Api.get(`/api/me/feed${query({ cursor, limit })}`);

  // ----- 기록 하나 -----
  const getPost = (address, no) => orNull(Api.get(postUrl(address, no)));
  const addView = (address, no) => Api.post(`${postUrl(address, no)}/views`);

  // data: { title, content, category_id, topic_slug, tags, visibility, cover_image_id, client_token } → { no, url }
  async function savePost(address, data, no) {
    return no ? Api.patch(postUrl(address, no), data) : Api.post(`${blogUrl(address)}/posts`, data);
  }

  const deletePost = (address, no) => Api.delete(postUrl(address, no));

  // { liked, like_count }
  const setLike = (address, no, on) => (on
    ? Api.put(`${postUrl(address, no)}/like`)
    : Api.delete(`${postUrl(address, no)}/like`));

  // ----- 댓글 -----
  // { items: [Comment], count }
  const getComments = (address, no) => Api.get(`${postUrl(address, no)}/comments`);
  const addComment = (address, no, content, clientToken) => Api.post(`${postUrl(address, no)}/comments`, { content, client_token: clientToken });
  const deleteComment = (id) => Api.delete(`/api/comments/${id}`);

  // ----- 내 정보 -----
  // data: { nickname?, profile_image_id? (null 이면 사진 지우기) } → { user }
  async function updateMe(data) {
    const result = await Api.patch('/api/me', data);
    await Auth.refresh();
    return result.user;
  }

  // { available, reason: null | 'INVALID' | 'TAKEN' }
  const nicknameAvailable = (nickname) => Api.get(`/api/auth/nickname-available${query({ nickname })}`);

  // ----- 사진 -----
  // { id, url, thumb_url, width, height }
  const uploadImage = (file) => Api.upload('/api/images', file);

  return {
    getTopics,
    getBlog,
    getMyBlog,
    checkAddress,
    createBlog,
    updateBlog,
    setNeighbor,
    getRooms,
    addRoom,
    getTags,
    listPosts,
    newPosts,
    topicPosts,
    neighborFeed,
    getPost,
    addView,
    savePost,
    deletePost,
    setLike,
    getComments,
    addComment,
    deleteComment,
    uploadImage,
    updateMe,
    nicknameAvailable,
  };
})();
